"""
agent.py - Antigravity AI Agent Integration

Dua mode koneksi ke AI:

  MODE 1 — Antigravity SDK (FULL, via agy CLI)
  ─────────────────────────────────────────────
  Pakai `google-antigravity` Python SDK.
  SDK otomatis membaca kredensial dari ~/.gemini/ yang dibuat oleh `agy` CLI.
  Cara aktifkan:
    1. pip install google-antigravity
    2. agy               ← jalankan sekali untuk login/autentikasi
    3. Setelah itu, SDK langsung konek ke Antigravity yang sama

  MODE 2 — Gemini API langsung (FALLBACK)
  ────────────────────────────────────────
  Pakai `google-generativeai` + GEMINI_API_KEY.
  Tidak perlu agy CLI, tapi tidak punya tool-use / capabilities penuh.
"""

import asyncio
import sys
import os
from pathlib import Path
from typing import AsyncIterator, Optional

# Coba import Antigravity SDK
try:
    from google.antigravity import Agent, LocalAgentConfig, CapabilitiesConfig
    from google.antigravity.utils.interactive import run_interactive_loop
    AGY_AVAILABLE = True
except ImportError:
    AGY_AVAILABLE = False


# ============================================================
# CEK KREDENSIAL agy CLI
# ============================================================

def is_agy_authenticated() -> bool:
    """
    Cek apakah user sudah login ke Antigravity via `agy` CLI.
    SDK membaca kredensial dari ~/.gemini/antigravity-cli/
    """
    agy_config_dir = Path.home() / ".gemini" / "antigravity-cli"
    return agy_config_dir.exists() and any(agy_config_dir.iterdir())


def get_auth_status() -> dict:
    """
    Kembalikan status lengkap autentikasi.
    """
    sdk_ok    = AGY_AVAILABLE
    agy_ok    = is_agy_authenticated() if sdk_ok else False
    api_key   = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    genai_ok  = False
    try:
        import google.generativeai
        genai_ok = True
    except ImportError:
        pass

    return {
        "sdk_installed":    sdk_ok,
        "agy_authenticated": agy_ok,
        "full_mode":        sdk_ok and agy_ok,     # Antigravity penuh
        "fallback_mode":    genai_ok and bool(api_key),  # Gemini API
        "api_key":          api_key,
        "genai_installed":  genai_ok,
    }


from ui.tui import (
    print_ai_bubble, print_ai_token, print_ai_done,
    print_user_bubble, info, error, warn, Spinner
)
from ui.colors import C, colorize


# ============================================================
# SYSTEM INSTRUCTION
# ============================================================

SYSTEM_PROMPT = """
Kamu adalah asisten developer expert bernama AGY (Antigravity), 
khusus membantu developer yang bekerja dari HP Android via Termux.

Kemampuan utamamu:
1. Membantu membuat & scaffold project (Python, Node.js, React, FastAPI, dll)
2. Menjelaskan kode, debug, dan review code
3. Membantu konfigurasi Docker di Termux
4. Menjalankan perintah terminal yang relevan
5. Memberikan saran best practice untuk mobile development workflow

Gaya komunikasi:
- Gunakan Bahasa Indonesia yang ramah dan lugas
- Berikan contoh kode yang langsung bisa dijalankan
- Selalu pertimbangkan keterbatasan HP (RAM, layar kecil)
- Prioritaskan solusi yang ringan dan efisien
""".strip()


# ============================================================
# AGENT WRAPPER
# ============================================================

class AndroidAgent:
    """
    Wrapper untuk Antigravity SDK Agent.
    
    Otomatis memilih mode terbaik yang tersedia:
      - MODE FULL : Antigravity SDK + agy credentials
      - MODE FALLBACK: Gemini API + GEMINI_API_KEY
    """
    
    def __init__(self, system_prompt: str = SYSTEM_PROMPT, silent: bool = False):
        self.system_prompt = system_prompt
        self._status = get_auth_status()
        
        if not silent:
            self._print_mode_badge()
    
    def _print_mode_badge(self):
        """Tampilkan badge mode koneksi yang aktif."""
        s = self._status
        if s["full_mode"]:
            badge = colorize(" ⚡ ANTIGRAVITY FULL ", C.BOLD, C.BG_CYAN, C.BLACK)
            desc  = colorize("Terhubung ke Antigravity AI via agy CLI", C.DIM)
        elif s["fallback_mode"]:
            badge = colorize(" ⭗ GEMINI FALLBACK ", C.BOLD, C.BG_MAGENTA, C.BLACK)
            desc  = colorize("Menggunakan Gemini API langsung (tanpa tool-use)", C.DIM)
        else:
            badge = colorize(" ⚠  TIDAK TERKONEKSI ", C.BOLD, C.BG_BLACK, C.BRIGHT_RED)
            desc  = colorize("Jalankan: actl config  atau  agy", C.DIM, C.BRIGHT_RED)
        print(f"  {badge}  {desc}")
        print()
    
    def _build_config(self) -> "LocalAgentConfig":
        return LocalAgentConfig(
            system_instructions=self.system_prompt,
            capabilities=CapabilitiesConfig(),
        )
    
    async def chat_stream(self, user_input: str):
        """
        Kirim pesan dan stream respons.
        Prioritas: Antigravity SDK (full) → Gemini API (fallback) → error.
        """
        s = self._status
        
        if s["full_mode"]:
            # ── MODE 1: Antigravity SDK via agy credentials ──
            config = self._build_config()
            async with Agent(config) as agent:
                response = await agent.chat(user_input)
                async for token in response:
                    yield token
        
        elif s["fallback_mode"]:
            # ── MODE 2: Gemini API langsung ──
            async for token in self._fallback_chat(user_input):
                yield token
        
        else:
            # ── Tidak ada koneksi ──
            yield "⚠️  Tidak ada koneksi AI yang aktif.\n\n"
            yield "Pilih salah satu cara untuk mengaktifkan:\n\n"
            yield "  [OPSI 1] Antigravity SDK (Full Mode)\n"
            yield "  ─────────────────────────────────────\n"
            yield "  pip install google-antigravity\n"
            yield "  agy   ← jalankan & ikuti proses login\n\n"
            yield "  [OPSI 2] Gemini API Key (Fallback Mode)\n"
            yield "  ─────────────────────────────────────────\n"
            yield "  actl config  ← masukkan GEMINI_API_KEY\n"
            yield "  Dapatkan key gratis: https://aistudio.google.com/app/apikey\n"
    
    async def chat_once(self, user_input: str) -> str:
        """Kirim pesan dan tunggu respons lengkap (non-streaming)."""
        full = ""
        async for token in self.chat_stream(user_input):
            full += token
        return full
    
    async def _fallback_chat(self, user_input: str):
        """
        Fallback: gunakan Gemini API langsung jika SDK tidak tersedia.
        Membutuhkan GEMINI_API_KEY atau GOOGLE_API_KEY di environment.
        """
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        
        if not api_key:
            yield "⚠️  Error: Tidak ada API key.\n"
            yield "Set environment variable: export GEMINI_API_KEY='your-key'\n"
            yield "Dapatkan key di: https://aistudio.google.com/app/apikey\n"
            return
        
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(
                "gemini-2.0-flash",
                system_instruction=self.system_prompt
            )
            response = model.generate_content(user_input, stream=True)
            for chunk in response:
                if chunk.text:
                    yield chunk.text
        except ImportError:
            yield "⚠️  Error: google-generativeai tidak terinstall.\n"
            yield "Jalankan: pip install google-generativeai\n"
        except Exception as e:
            yield f"⚠️  Error API: {e}\n"


# ============================================================
# INTERACTIVE CHAT SESSION
# ============================================================

async def run_chat_session():
    """
    Jalankan sesi chat interaktif dengan Antigravity AI.
    Loop sampai user mengetik 'exit', 'quit', atau Ctrl+C.
    """
    from ui.tui import section_header, divider, prompt
    
    section_header("💬 CHAT SESSION", C.BRIGHT_MAGENTA)
    
    info("Ketik pesan untuk chat dengan Antigravity AI.")
    info("Ketik 'exit' atau tekan Ctrl+C untuk keluar.")
    divider()
    
    agent = AndroidAgent()
    history_count = 0
    
    while True:
        try:
            # Ambil input user
            user_input = prompt("Kamu")
            
            if not user_input:
                continue
            
            if user_input.lower() in ("exit", "quit", "keluar", "/exit", "/quit"):
                info(f"Sesi berakhir. Total pesan: {history_count}")
                break
            
            # Tampilkan bubble user
            print_user_bubble(user_input)
            
            # Stream respons AI
            print_ai_bubble("", streaming=True)
            
            async for token in agent.chat_stream(user_input):
                print_ai_token(token)
            
            print_ai_done()
            history_count += 1
            divider()
            
        except KeyboardInterrupt:
            print()
            info(f"Sesi dihentikan. Total pesan: {history_count}")
            break
        except Exception as e:
            error(f"Error: {e}")


def start_chat():
    """Entry point untuk perintah `actl chat`."""
    asyncio.run(run_chat_session())


# ============================================================
# QUICK TASK (SINGLE PROMPT)
# ============================================================

async def run_quick_task(prompt_text: str) -> str:
    """
    Jalankan satu tugas AI tanpa sesi interaktif.
    Digunakan oleh scaffold.py dan modul lain.
    """
    agent = AndroidAgent()
    with Spinner(f"AI sedang memproses..."):
        result = await agent.chat_once(prompt_text)
    return result


def quick_task(prompt_text: str) -> str:
    """Sync wrapper untuk run_quick_task."""
    return asyncio.run(run_quick_task(prompt_text))
