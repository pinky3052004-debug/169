import os
import subprocess

# Rclone ဖြင့် Google Drive (NanNanIphone) မှ ဖိုင်များကို ဆွဲထုတ်ခြင်း (အများဆုံး ၁၀ ခု)
os.system("rclone copy gdrive:NanNanIphone ./input_folder --max-depth 1")

if not os.path.exists("processed.txt"):
    open("processed.txt", "w").close()

with open("processed.txt", "r") as f:
    processed_files = set(f.read().splitlines())

files = [f for f in os.listdir("input_folder") if f.endswith((".mp4", ".mov", ".mkv"))]
unprocessed_files = [f for f in files if f not in processed_files][:10] # တစ်ကြိမ်လျှင် ၁၀ ခုသာ

if not unprocessed_files:
    print("လုပ်ဆောင်ရန် ဗီဒီယိုအသစ် မရှိတော့ပါ။")
    exit(0)

for file in unprocessed_files:
    input_path = os.path.join("input_folder", file)
    output_path = f"output_{file}"
    
    print(f"Converting: {file}")
    # 9:16 to 16:9 Blur Background FFmpeg Command
    cmd = f"ffmpeg -i '{input_path}' -filter_complex '[0:v]scale=ih*16/9:ih,boxblur=s=40:p=3[bg];[0:v]scale=-1:1080[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2' -c:a copy '{output_path}'"
    subprocess.run(cmd, shell=True, check=True)
    
    # NanNanIphone2 သို့ တင်ခြင်း
    os.system(f"rclone copy '{output_path}' gdrive:NanNanIphone2")
    
    # ပြီးသွားသော ဖိုင်များကို မှတ်တမ်းတင်ခြင်း
    with open("processed.txt", "a") as f:
        f.write(file + "\n")

print("ဤတစ်ကြိမ်အတွက် ဗီဒီယို ၁၀ ခု ပြောင်းလဲပြီးပါပြီ။")
