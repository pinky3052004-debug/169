import os
import subprocess

# input_folder မရှိပါက ဖန်တီးရန်
os.makedirs("input_folder", exist_ok=True)

print("Google Drive မှ ဖိုင်များကို ဆွဲထုတ်နေပါပြီ...")
os.system("rclone copy mydrive:NanNanIphone ./input_folder --max-depth 1")

if not os.path.exists("processed.txt"):
    open("processed.txt", "w").close()

with open("processed.txt", "r") as f:
    processed_files = set(f.read().splitlines())

if not os.path.exists("input_folder"):
    print("input_folder မရှိပါ။")
    exit(1)

files = [f for f in os.listdir("input_folder") if f.endswith((".mp4", ".mov", ".mkv", ".MP4", ".MOV"))]
unprocessed_files = [f for f in files if f not in processed_files][:10] # တစ်ကြိမ်လျှင် ၁၀ ခုသာ

if not unprocessed_files:
    print("လုပ်ဆောင်ရန် ဗီဒီယိုအသစ် မရှိတော့ပါ။")
    exit(0)

for file in unprocessed_files:
    input_path = os.path.join("input_folder", file)
    output_path = f"output_{file}"
    
    print(f"Converting: {file}")
    # 9:16 to 16:9 Blur Background (Updated with gblur)
    cmd = f"ffmpeg -i '{input_path}' -filter_complex '[0:v]scale=ih*16/9:ih,gblur=sigma=20[bg];[0:v]scale=-1:1080[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2' -c:a copy '{output_path}'"
    subprocess.run(cmd, shell=True, check=True)
    
    print(f"Uploading: {output_path} to NanNanIphone2")
    os.system(f"rclone copy '{output_path}' mydrive:NanNanIphone2")
    
    # ပြီးသွားသော ဖိုင်များကို မှတ်တမ်းတင်ခြင်း
    with open("processed.txt", "a") as f:
        f.write(file + "\n")
        
    # ဒေသတွင်း ဖိုင်ဟောင်းများကို ရှင်းလင်းခြင်း
    if os.path.exists(input_path):
        os.remove(input_path)
    if os.path.exists(output_path):
        os.remove(output_path)

print("ဤတစ်ကြိမ်အတွက် ဗီဒီယို ၁၀ ခု ပြောင်းလဲပြီးပါပြီ။")
