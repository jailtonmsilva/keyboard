import sys
import os
import wmi
import ctypes
import customtkinter as ctk
from ctypes import wintypes
from PIL import Image, ImageDraw, ImageOps

from love_nic.config.constants import WINDOW_SIZE, WINDOW_TITLE

# =======================================================
# UTILITÁRIOS PARA O EXECUTÁVEL E ARQUIVOS
# =======================================================
def resolver_caminho(caminho_relativo):
    """Garante que o app ache os arquivos tanto rodando no VSCode quanto no .exe compilado."""
    try:
        # PyInstaller cria uma pasta temporária e armazena o caminho no _MEIPASS
        caminho_base = sys._MEIPASS
    except Exception:
        # Se nao estiver rodando como .exe, usa a pasta do arquivo atual
        caminho_base = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(caminho_base, caminho_relativo)

def mci_send(command):
    """Envia comandos para o player nativo do Windows (MCI)."""
    buffer = ctypes.create_unicode_buffer(255)
    error_code = ctypes.windll.winmm.mciSendStringW(command, buffer, 254, 0)
    return error_code, buffer.value

def obter_id_teclado_interno():
    """Busca o ID do teclado nativo do notebook via WMI."""
    try:
        wmi_obj = wmi.WMI()
        for teclado in wmi_obj.Win32_Keyboard():
            if teclado.DeviceID.startswith("ACPI"):
                return teclado.DeviceID
    except Exception as e:
        print(f"Erro ao buscar teclado via WMI: {e}")
    return None

# =======================================================
# CONFIGURAÇÕES DO HARDWARE E API DO WINDOWS
# =======================================================
# Busca dinâmica do teclado, com um fallback (Plano B) de segurança
TECLADO_ID = obter_id_teclado_interno()

if not TECLADO_ID:
    print("⚠️ Teclado ACPI não encontrado dinamicamente.")
    TECLADO_ID = r"ACPI\PNP0303\4&12A3B4C5&0"  # O seu ID original como garantia

# Constantes da API do Windows (cfgmgr32.dll)
CR_SUCCESS = 0
DN_STARTED = 0x00000008
CM_PROB_DISABLED = 22

try:
    cfgmgr32 = ctypes.WinDLL('cfgmgr32.dll')

    # Configuração das funções C nativas para Python
    CM_Locate_DevNodeW = cfgmgr32.CM_Locate_DevNodeW
    CM_Locate_DevNodeW.argtypes = [ctypes.POINTER(ctypes.c_ulong), wintypes.LPCWSTR, ctypes.c_ulong]
    CM_Locate_DevNodeW.restype = ctypes.c_ulong

    CM_Disable_DevNode = cfgmgr32.CM_Disable_DevNode
    CM_Disable_DevNode.argtypes = [ctypes.c_ulong, ctypes.c_ulong]
    CM_Disable_DevNode.restype = ctypes.c_ulong

    CM_Enable_DevNode = cfgmgr32.CM_Enable_DevNode
    CM_Enable_DevNode.argtypes = [ctypes.c_ulong, ctypes.c_ulong]
    CM_Enable_DevNode.restype = ctypes.c_ulong

    CM_Get_DevNode_Status = cfgmgr32.CM_Get_DevNode_Status
    CM_Get_DevNode_Status.argtypes = [ctypes.POINTER(ctypes.c_ulong), ctypes.POINTER(ctypes.c_ulong), ctypes.c_ulong, ctypes.c_ulong]
    CM_Get_DevNode_Status.restype = ctypes.c_ulong

except Exception as e:
    print(f"Erro ao carregar a API do Windows: {e}")
    sys.exit(1)

# =======================================================
# FUNÇÕES DE CONTROLE DO TECLADO VIA API DO WINDOWS
# =======================================================
def is_admin():
    """Verifica se o script tem privilégios de administrador."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

def get_dev_node(instance_id):
    """Localiza o nó do dispositivo no Windows."""
    dev_inst = ctypes.c_ulong(0)
    if CM_Locate_DevNodeW(ctypes.byref(dev_inst), instance_id, 0) == CR_SUCCESS:
        return dev_inst
    return None

def is_device_enabled(instance_id):
    """Verifica se o teclado está ativado usando a API nativa."""
    dev_inst = get_dev_node(instance_id)
    if dev_inst:
        status = ctypes.c_ulong(0)
        problem = ctypes.c_ulong(0)
        if CM_Get_DevNode_Status(ctypes.byref(status), ctypes.byref(problem), dev_inst, 0) == CR_SUCCESS:
            if problem.value == CM_PROB_DISABLED:
                return False
            if status.value & DN_STARTED:
                return True
    return False

def set_device_state(instance_id, enable=True):
    """Ativa ou desativa o teclado usando a API nativa."""
    dev_inst = get_dev_node(instance_id)
    if dev_inst:
        if enable:
            return CM_Enable_DevNode(dev_inst, 0) == CR_SUCCESS
        else:
            return CM_Disable_DevNode(dev_inst, 0) == CR_SUCCESS
    return False

# Reinicia pedindo privilégios se não for admin
if not is_admin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit()

# =======================================================
# INTERFACE GRÁFICA (TELA)
# =======================================================
class LoveApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Estado dos controles de midia
        self.media_alias = "lovebgm"
        self.music_ready = False
        self.is_playing = False
        self.is_paused = False
        self.is_muted = False
        self.volume_level = 700
        self.previous_volume = self.volume_level

        # Configurações da Janela Fixa
        self.title(WINDOW_TITLE)
        self.geometry(WINDOW_SIZE)
        self.resizable(False, False)
        ctk.set_appearance_mode("light")

        # Define o icone da janela (barra de titulo) no runtime.
        try:
            caminho_icone = resolver_caminho(os.path.join("projeto", "src", "img", "love_nic.ico"))
            self.iconbitmap(caminho_icone)
        except Exception:
            pass
        
        # Grid: lado direito com largura minima para caber titulo + switch
        self.grid_columnconfigure(0, weight=4)
        self.grid_columnconfigure(1, weight=5, minsize=440)
        self.grid_rowconfigure(0, weight=1)

        # ---- PAINEL ESQUERDO (FOTO) ----
        self.left_frame = ctk.CTkFrame(self, fg_color="#D8D1CC", corner_radius=15)
        self.left_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        try:
            caminho_imagem = resolver_caminho(os.path.join("projeto", "src", "img", "foto.jpeg"))
            img_data = Image.open(caminho_imagem).convert("RGBA")

            # Mantem proporcao 1:1 da imagem original em um quadro quadrado.
            image_size = (360, 360)
            img_data = ImageOps.fit(img_data, image_size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))

            # Aplica cantos arredondados via mascara alfa.
            mask = Image.new("L", image_size, 0)
            draw = ImageDraw.Draw(mask)
            draw.rounded_rectangle((0, 0, image_size[0] - 1, image_size[1] - 1), radius=28, fill=255)
            img_data.putalpha(mask)

            self.my_image = ctk.CTkImage(light_image=img_data, dark_image=img_data, size=image_size)
            self.image_label = ctk.CTkLabel(self.left_frame, image=self.my_image, text="")
            self.image_label.pack(expand=True)
        except Exception as e:
            self.image_label = ctk.CTkLabel(self.left_frame, text=f"⚠️ Imagem não encontrada.\n{e}")
            self.image_label.pack(expand=True)

        # ---- PAINEL DIREITO (CONTROLES) ----
        self.right_frame = ctk.CTkFrame(self, fg_color="#F4F4F4", corner_radius=15)
        self.right_frame.grid(row=0, column=1, padx=(0, 20), pady=20, sticky="nsew")

        self.toggle_frame = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        self.toggle_frame.pack(fill="x", padx=30, pady=(40, 10))
        self.toggle_frame.grid_columnconfigure(0, weight=1)
        self.toggle_frame.grid_columnconfigure(1, weight=0)

        self.lbl_title_toggle = ctk.CTkLabel(self.toggle_frame, text="Teclado interno", font=("Arial", 28, "bold"), text_color="#1F1F1F")
        self.lbl_title_toggle.grid(row=0, column=0, sticky="w")

        # Botão Toggle 
        self.switch_var = ctk.StringVar(value="on")
        self.switch = ctk.CTkSwitch(
            self.toggle_frame,
            text="", 
            variable=self.switch_var,
            onvalue="on",
            offvalue="off",
            command=self.toggle_event,
            progress_color="#198754", # Verde quando habilitado
            fg_color="#DC3545",       # Vermelho quando desabilitado
            switch_width=55,
            switch_height=28
        )
        self.switch.grid(row=0, column=1, padx=(10, 0), sticky="e")

        self.desc_label = ctk.CTkLabel(
            self.right_frame, 
            text="Ativa ou desativa o teclado interno para uso\ncom teclados externos.", 
            justify="left", 
            font=("Arial", 13), 
            text_color="#4A4A4A"
        )
        self.desc_label.pack(anchor="w", padx=30, pady=(0, 40))

        # ---- MÚSICA (2 COLUNAS) ----
        self.lyrics_frame = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        self.lyrics_frame.pack(fill="both", expand=True, padx=10, pady=(0, 20))
        self.lyrics_frame.grid_columnconfigure(0, weight=1)
        self.lyrics_frame.grid_columnconfigure(1, weight=1)

        letra_coluna_1 = (
            "Se um dia eu te encontrar\nDo jeito que sonhei\nQuem sabe ser seu par\nPerfeito e te amar\n"
            "Do jeito que eu imaginei\n\nAo virar a esquina\nAtrás de uma cortina, me perder\nNo escuro com você\n"
            "Fogo na fogueira\nO seu beijo e o desejo em seu olhar\nAs flores no altar\n\nVéu e grinalda, Lua de mel\n"
            "Chuva de arroz e tudo depois\nDama de honra pega o buquê\nNinguém mais feliz que eu e você\n\n"
            "Mas se um dia eu te encontrar\nDo jeito que sonhei\nQuem sabe ser seu par\nPerfeito e te amar\n"
            "Do jeito que eu imaginei"
        )

        letra_coluna_2 = (
            "Ao virar a esquina\nAtrás de uma cortina, me perder\nNo escuro com você\nFogo na fogueira\n"
            "O seu beijo e o desejo em seu olhar\nAs flores no altar\n\nVéu e grinalda, Lua de mel\n"
            "Chuva de arroz e tudo depois\nDama de honra pega o buquê\nNinguém mais feliz que eu e você\n\n"
            "Ninguém mais feliz que eu e você\nNinguém mais feliz que eu e você\nNinguém mais feliz que eu e você\n"
            "Ninguém mais feliz que eu e você\n\nMas se um dia eu te encontrar\nDo jeito que sonhei\n"
            "Quem sabe ser seu par\nPerfeito e te amar\nDo jeito que eu imaginei"
        )

        self.lbl_letra1 = ctk.CTkLabel(self.lyrics_frame, text=letra_coluna_1, justify="center", font=("Arial", 12), text_color="#555555")
        self.lbl_letra1.grid(row=0, column=0, sticky="n")

        self.lbl_letra2 = ctk.CTkLabel(self.lyrics_frame, text=letra_coluna_2, justify="center", font=("Arial", 12), text_color="#555555")
        self.lbl_letra2.grid(row=0, column=1, sticky="n")

        # ---- LINHA SEPARADORA ----
        self.separator = ctk.CTkFrame(self.right_frame, fg_color="#D8D1CC", height=2)
        self.separator.pack(fill="x", padx=30, pady=(10, 20))

        # ---- CONTROLES DE MIDIA ----
        self.media_frame = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        self.media_frame.pack(anchor="center", padx=30, pady=(0, 20))

        self.btn_play_stop = ctk.CTkButton(
            self.media_frame,
            text="⏹",
            width=50,
            height=50,
            corner_radius=10,
            font=("Arial", 20, "bold"),
            command=self.toggle_play_stop
        )
        self.btn_play_stop.pack(side="left", padx=10)

        self.btn_pause = ctk.CTkButton(
            self.media_frame,
            text="⏸",
            width=50,
            height=50,
            corner_radius=10,
            font=("Arial", 20, "bold"),
            command=self.pause_music
        )
        self.btn_pause.pack(side="left", padx=10)

        self.btn_volume = ctk.CTkButton(
            self.media_frame,
            text="🔊",
            width=50,
            height=50,
            corner_radius=10,
            font=("Arial", 18, "bold"),
            command=self.toggle_volume
        )
        self.btn_volume.pack(side="left", padx=10)

        # Inicia musica em loop ao abrir a interface
        self.init_music()

        # Verifica o status do hardware e atualiza a interface ao abrir
        self.check_initial_status()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    # =======================================================
    # EVENTOS DA INTERFACE
    # =======================================================
    def check_initial_status(self):
        """Verifica como o teclado está no Windows e ajusta o botão visual."""
        if not TECLADO_ID:
            self.lbl_title_toggle.configure(text="Teclado não detectado")
            self.switch.configure(state="disabled")
            return

        if is_device_enabled(TECLADO_ID):
            self.switch.select()
            self.lbl_title_toggle.configure(text="Teclado interno  ON")
        else:
            self.switch.deselect()
            self.lbl_title_toggle.configure(text="Teclado interno OFF")

    def toggle_event(self):
        """Disparado quando o usuário clica no botão ON/OFF."""
        if not TECLADO_ID:
            return

        estado_atual = self.switch_var.get()
        
        if estado_atual == "on":
            sucesso = set_device_state(TECLADO_ID, enable=True)
            if sucesso:
                self.lbl_title_toggle.configure(text="Teclado interno  ON")
            else:
                self.switch.deselect()
        else:
            sucesso = set_device_state(TECLADO_ID, enable=False)
            if sucesso:
                self.lbl_title_toggle.configure(text="Teclado interno OFF")
            else:
                self.switch.select()

    def init_music(self):
        """Carrega o mp3 e inicia reproducao em loop usando player nativo do Windows."""
        music_path = resolver_caminho(os.path.join("projeto", "src", "mp3", "alianca.mp3"))
        if not os.path.exists(music_path):
            self.disable_media_controls()
            return

        open_cmd = f'open "{music_path}" type mpegvideo alias {self.media_alias}'
        error_code, _ = mci_send(open_cmd)
        if error_code != 0:
            self.disable_media_controls()
            return

        mci_send(f"setaudio {self.media_alias} volume to {self.volume_level}")
        mci_send(f"play {self.media_alias} repeat")
        self.music_ready = True
        self.is_playing = True
        self.is_paused = False
        self.btn_play_stop.configure(text="⏹")

    def disable_media_controls(self):
        self.music_ready = False
        self.is_playing = False
        self.is_paused = False
        self.btn_play_stop.configure(state="disabled")
        self.btn_pause.configure(state="disabled")
        self.btn_volume.configure(state="disabled")

    def toggle_play_stop(self):
        if not self.music_ready:
            return

        if self.is_playing:
            mci_send(f"stop {self.media_alias}")
            self.is_playing = False
            self.is_paused = False
            self.btn_play_stop.configure(text="▶")
            return

        mci_send(f"play {self.media_alias} repeat")
        self.is_playing = True
        self.is_paused = False
        self.btn_play_stop.configure(text="⏹")

    def pause_music(self):
        if not self.music_ready or not self.is_playing:
            return

        if self.is_paused:
            mci_send(f"resume {self.media_alias}")
            self.is_paused = False
        else:
            mci_send(f"pause {self.media_alias}")
            self.is_paused = True

    def toggle_volume(self):
        if not self.music_ready:
            return

        if self.is_muted:
            self.volume_level = self.previous_volume
            mci_send(f"setaudio {self.media_alias} volume to {self.volume_level}")
            self.btn_volume.configure(text="🔊")
            self.is_muted = False
            return

        self.previous_volume = self.volume_level
        mci_send(f"setaudio {self.media_alias} volume to 0")
        self.btn_volume.configure(text="🔇")
        self.is_muted = True

    def on_close(self):
        if self.music_ready:
            mci_send(f"stop {self.media_alias}")
            mci_send(f"close {self.media_alias}")
        self.destroy()

def main():
    app = LoveApp()
    app.mainloop()


if __name__ == "__main__":
    main()
