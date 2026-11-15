#!/usr/bin/env python3
"""One terminal menu for running the Transit Atlas locally."""
import json
import os
import pathlib
import subprocess
import sys
import time
from urllib.request import urlopen

ROOT=pathlib.Path(__file__).resolve().parents[1]
DATA=pathlib.Path(os.environ.get('ATLAS_DATA_DIR',ROOT/'data'))
server=None
server_log=None
ollama=None
ollama_log=None

def clear_screen():
 if sys.stdin.isatty() and sys.stdout.isatty():
  os.system('cls' if os.name == 'nt' else 'clear')

def online(url):
 try:
  with urlopen(url,timeout=1):return True
 except Exception:return False

def compact_status():
 atlas='●' if online('http://127.0.0.1:8000/api/v1/meta') else '○'
 ollama_state='●' if online('http://127.0.0.1:11434/api/tags') else '○'
 model=os.environ.get('OLLAMA_MODEL','qwen3:1.7b')
 return f'Atlas {atlas}  Ollama {ollama_state}  Model {model}'

def pause():
 input('\nPress Enter to return to the menu...')

def run(label, command):
 print(f'\n--- {label} ---')
 try:
  result=subprocess.run(command,cwd=ROOT,check=False)
  print(f'\n{label}: exit {result.returncode}')
 except KeyboardInterrupt:
  print('\nInterrupted.')
 pause()

def start_server(pause_after=True):
 global server,server_log
 if server and server.poll() is None:
  print('Server is already running at http://127.0.0.1:8000')
  if pause_after:pause()
  return
 DATA.mkdir(exist_ok=True)
 server_log=open(DATA/'atlas-tui-server.log','a',encoding='utf-8')
 server=subprocess.Popen([sys.executable,str(ROOT/'server.py')],cwd=ROOT,stdout=server_log,stderr=subprocess.STDOUT)
 time.sleep(.5)
 print('Server started at http://127.0.0.1:8000')
 print(f'Log: {DATA/"atlas-tui-server.log"}')
 if pause_after:pause()

def stop_server(pause_after=True):
 global server,server_log
 if not server or server.poll() is not None:
  print('Server is not running.')
 else:
  server.terminate()
  try:server.wait(timeout=5)
  except subprocess.TimeoutExpired:server.kill();server.wait()
  print('Server stopped.')
 if server_log:server_log.close();server_log=None
 server=None
 if pause_after:pause()

def start_ollama(pause_after=True):
 global ollama,ollama_log
 if ollama and ollama.poll() is None:
  print('Ollama is already running.')
  if pause_after:pause()
  return
 try:
  with urlopen('http://127.0.0.1:11434/api/tags',timeout=1):
   print('Ollama is already running outside the TUI.')
   if pause_after:pause()
   return
 except Exception:
  pass
 try:
  ollama_log=open(DATA/'atlas-tui-ollama.log','a',encoding='utf-8')
  ollama=subprocess.Popen(['ollama','serve'],cwd=ROOT,stdout=ollama_log,stderr=subprocess.STDOUT)
  time.sleep(1)
  print('Ollama started at http://127.0.0.1:11434')
  print(f'Log: {DATA/"atlas-tui-ollama.log"}')
 except FileNotFoundError:
  print('Ollama command not found. Install Ollama or start it outside the TUI.')
 if pause_after:pause()

def stop_ollama(pause_after=True):
 global ollama,ollama_log
 if not ollama or ollama.poll() is not None:
  print('TUI-started Ollama is not running.')
 else:
  ollama.terminate()
  try:ollama.wait(timeout=5)
  except subprocess.TimeoutExpired:ollama.kill();ollama.wait()
  print('Ollama stopped.')
 if ollama_log:ollama_log.close();ollama_log=None
 ollama=None
 if pause_after:pause()

def stack_status():
 print('\n--- Local AI stack ---')
 for label,url in [('Atlas API','http://127.0.0.1:8000/api/v1/meta'),('Ollama API','http://127.0.0.1:11434/api/tags')]:
  try:
   with urlopen(url,timeout=2) as response:print(f'{label:<12} online ({response.status})')
  except Exception as exc:print(f'{label:<12} offline ({exc.__class__.__name__})')
 try:
  result=subprocess.run(['ollama','list'],cwd=ROOT,check=False,text=True,capture_output=True)
  print('\nInstalled Ollama models:')
  print(result.stdout.strip() or '(none found)')
 except FileNotFoundError:print('Ollama CLI    not installed/on PATH')
 pause()

def chat_with_atlas():
 model=os.environ.get('OLLAMA_MODEL','qwen3:1.7b')
 print(f'Launching Percival with {model}. Type quit to return to the TUI.')
 run('Ollama MCP chat',[sys.executable,str(ROOT/'scripts/ollama_mcp_chat.py'),'--model',model])

def start_stack():
 print('\nStarting Atlas and Ollama...')
 start_server(pause_after=False)
 start_ollama(pause_after=False)
 print('Local stack ready. Use Chat to talk to Percival.')

def advanced_menu():
 while True:
  print('''\n--- Advanced controls ---
[1] Start web app
[2] Stop web app
[3] Prepare core feeds
[4] Prepare core + optional MTA/LIRR
[5] External smoke test
[6] External smoke test + routing
[7] Run tests
[8] Feed status
[9] Local AI stack status
[10] Start Ollama
[11] Chat with Atlas via Ollama
[12] Stop TUI-started Ollama
[b] Back''')
  choice=input('Advanced: ').strip().lower()
  if choice=='1':start_server()
  elif choice=='2':stop_server()
  elif choice=='3':run('Core feed preparation',[sys.executable,str(ROOT/'scripts/prepare_data.py')])
  elif choice=='4':run('Core + optional MTA preparation',[sys.executable,str(ROOT/'scripts/prepare_data.py'),'--include-optional'])
  elif choice=='5':run('External smoke test',[sys.executable,str(ROOT/'scripts/external_smoke.py')])
  elif choice=='6':run('External smoke test with routing',[sys.executable,str(ROOT/'scripts/external_smoke.py'),'--routing','--date',os.environ.get('ATLAS_DATE','2026-11-17')])
  elif choice=='7':run('Python tests',[sys.executable,'-m','unittest','discover','-s','tests','-v'])
  elif choice=='8':status()
  elif choice=='9':stack_status()
  elif choice=='10':start_ollama()
  elif choice=='11':chat_with_atlas()
  elif choice=='12':stop_ollama()
  elif choice=='b':return
  else:print('Choose a listed option.')

def status():
 print('\n--- Feed status ---')
 path=DATA/'sources.json'
 if not path.exists():print('No feed registry yet. Run a prepare action.');pause();return
 for source in json.loads(path.read_text()):
  mark='optional' if source.get('optional') else 'core'
  print(f"{source['id']:<14} {source.get('status','unknown'):<18} {mark:<8} {source.get('service_start','')}..{source.get('service_end','')}")
 pause()

def main():
 if '--advanced' in sys.argv:
  advanced_menu();return
 while True:
  clear_screen()
  print('╭──────────────────────────────────────────────╮')
  print('│ PERCIVAL · local transit companion            │')
  print('╰──────────────────────────────────────────────╯')
  print(compact_status())
  print('')
  print('  [s] Start stack     [c] Chat')
  print('  [r] Refresh status   [a] Advanced')
  print('  [q] Quit')
  try:choice=input('\n  percival> ').strip().lower()
  except (EOFError,KeyboardInterrupt):choice='q'
  if choice in ('s','start','1'):start_stack()
  elif choice in ('c','chat','2'):
   if not online('http://127.0.0.1:8000/api/v1/meta'):start_server(pause_after=False)
   if not online('http://127.0.0.1:11434/api/tags'):start_ollama(pause_after=False)
   chat_with_atlas()
  elif choice in ('r','refresh','3'):
   print('\n'+compact_status());time.sleep(1)
  elif choice in ('a','advanced','4'):advanced_menu()
  elif choice in ('q','quit','0'):
   if server and server.poll() is None:stop_server(pause_after=False)
   if ollama and ollama.poll() is None:stop_ollama(pause_after=False)
   print('Goodbye.');return
  else:
   print('Unknown command. Press a, c, r, s or q.')

if __name__=='__main__':main()
