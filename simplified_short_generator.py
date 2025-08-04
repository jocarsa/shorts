#!/usr/bin/env python3

import subprocess
import sys
import os
import time

def obtener_ids_del_canal(canal_url):
    print("🔍 Obteniendo lista de videos del canal...")
    try:
        resultado = subprocess.run(
            ['yt-dlp', '--flat-playlist', '--get-id', canal_url],
            capture_output=True, text=True, check=True
        )
        ids = resultado.stdout.strip().split('\n')
        print(f"✅ {len(ids)} vídeos encontrados.")
        return ids
    except subprocess.CalledProcessError as e:
        print("❌ Error al obtener los IDs de los vídeos:")
        print(e.stderr)
        sys.exit(1)

def obtener_titulo(video_url):
    resultado = subprocess.run(['yt-dlp', '--get-title', video_url], capture_output=True, text=True)
    return resultado.stdout.strip().replace('/', '-').replace(':', '-')

def extraer_fragmento(input_file, output_file, start_time, crop_filter, width, height):
    cmd = [
        'ffmpeg', '-y', '-ss', str(start_time), '-i', input_file,
        '-t', '60',
        '-vf', f'{crop_filter},scale={width}:{height}',
        '-an',
        '-preset', 'ultrafast',
        output_file
    ]
    subprocess.run(cmd, check=True)

def procesar_video(video_id):
    video_url = f'https://www.youtube.com/watch?v={video_id}'
    titulo = obtener_titulo(video_url)
    epoch = int(time.time())
    tmp_file = f"tmp_{video_id}.mp4"

    print(f"⬇️ Descargando: {titulo}")
    subprocess.run([
        'yt-dlp', '-f', 'bestvideo+bestaudio', '--merge-output-format', 'mp4',
        video_url, '-o', tmp_file
    ], check=True)

    print("📊 Analizando resolución...")
    res_output = subprocess.check_output([
        'ffprobe', '-v', 'error', '-select_streams', 'v:0',
        '-show_entries', 'stream=width,height',
        '-of', 'csv=p=0:s=x', tmp_file
    ])
    res = res_output.decode().strip()
    width, height = map(int, res.split('x'))

    target_width = int(height * 9 / 16)
    if target_width > width:
        target_width = width
        target_height = int(width * 16 / 9)
    else:
        target_height = height

    # Paridad para H.264
    target_width = (target_width // 2) * 2
    target_height = (target_height // 2) * 2

    x_offset = (width - target_width) // 2
    y_offset = (height - target_height) // 2

    crop_filter = f"crop={target_width}:{target_height}:{x_offset}:{y_offset}"

    print("⏱️ Obteniendo duración...")
    dur_output = subprocess.check_output([
        'ffprobe', '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        tmp_file
    ])
    duration = float(dur_output.decode().strip())

    puntos = [0, duration * 0.33, duration * 0.66, max(0, duration - 60)]

    for idx, start_time in enumerate(puntos):
        nombre_salida = f"Screensaver {titulo} #{idx+1} #shorts {epoch}.mp4"
        print(f"🎬 Generando fragmento {idx+1}/4 desde {int(start_time)}s...")
        extraer_fragmento(tmp_file, nombre_salida, int(start_time), crop_filter, target_width, target_height)

    os.remove(tmp_file)

def procesar_videos(ids):
    for i, video_id in enumerate(ids, 1):
        print(f"\n📽️ Procesando vídeo {i}/{len(ids)}")
        try:
            procesar_video(video_id)
        except subprocess.CalledProcessError as e:
            print(f"⚠️ Error procesando vídeo {video_id}: {e}")
        time.sleep(5)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python3 simplified_short_generator.py <URL_DEL_CANAL>")
        sys.exit(1)

    canal_url = sys.argv[1]
    video_ids = obtener_ids_del_canal(canal_url)
    procesar_videos(video_ids)

