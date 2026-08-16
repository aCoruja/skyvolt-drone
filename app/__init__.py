import os

if os.name == "nt":
    os.system("")

BLUE = "\033[38;5;39m"
YELLOW = "\033[38;5;220m"
CYAN = "\033[38;5;51m"
GREEN = "\033[38;5;82m"
WHITE = "\033[97m"
BOLD = "\033[1m"
RESET = "\033[0m"

banner = f"""
{BLUE}{BOLD}   _____ _  __ __     __{YELLOW}      __  ____  _      _______ 
{BLUE}{BOLD}  / ____| |/ / \ \   / / {YELLOW}     \ \  / / / __ \| |    |__   __|
{BLUE}{BOLD} | (___ | ' /   \ \_/ /  {YELLOW}      \ \/ / | |  | | |       | |   
{BLUE}{BOLD}  \___ \|  <     \   /   {YELLOW}       \  /  | |  | | |       | |   
{BLUE}{BOLD}  ____) | . \     | |    {YELLOW}        \/   | |__| | |____   | |   
{BLUE}{BOLD} |_____/|_|\_\    |_|    {YELLOW}             \____/|______|  |_|  ⚡{RESET}

{CYAN} ───────────────────────────────────────────────────────────────
  ⚡ {WHITE}{BOLD}SKYVOLT{RESET}{CYAN} | Sistema de Monitoramento Elétrico Residencial
 ───────────────────────────────────────────────────────────────{RESET}

{YELLOW}{BOLD} 👥 EQUIPE DE DESENVOLVIMENTO:{RESET}
  ⚡ {WHITE}Matheus Dapper{RESET}
  ⚡ {WHITE}Vitoria{RESET}
  ⚡ {WHITE}Sofia Moura(Robertson){RESET}

{CYAN} ───────────────────────────────────────────────────────────────{RESET}
 🚀 {GREEN}{BOLD}Iniciando aplicação gráfica PyQt5...{RESET}
"""

print(banner)
