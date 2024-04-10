import os
from tqdm import tqdm

class JadxToText:
    def __init__(self, source_folder=None, output_file="merged_code.txt") -> None:
        if source_folder:
            self.source_folder = source_folder
        else:
            self.source_folder = input("Укажите путь до папки source: ").replace('"', "")
            while not os.path.exists(self.source_folder):
                self.source_folder = input("Такого каталога не существует. Укажите другой: ").replace('"', "")

        self.source_folder = fr"{self.source_folder}".replace('"', '')
        self.output_file = output_file

    def merge_source_to_txt(self):
        with open(self.output_file, 'w') as merged_file:
            all_files = []
            for root, dirs, files in os.walk(self.source_folder):
                for file in files:
                    if file.endswith('.java'):
                        all_files.append(os.path.join(root, file))

            with tqdm(total=len(all_files), desc='Processing files') as pbar:
                for file_path in all_files:
                    try:
                        with open(file_path, 'r') as java_file:
                            merged_file.write(f"{'=' * 50}\n")
                            merged_file.write(f"File: {file_path}\n")
                            merged_file.write(f"{'=' * 50}\n")
                            merged_file.write(java_file.read())
                            merged_file.write('\n\n')
                    except UnicodeDecodeError:
                        print(f"[LOG] UnicodeDecodeError in file: {file_path.replace(self.source_folder, '')}\n")
                    
                    pbar.update(1)
                    pbar.set_description(f'Processing: {file_path.replace(self.source_folder, "")}')

        print(f"[LOG] Done! All code saved in {self.output_file}\n")

if __name__ == "__main__":
    source_path = input(f"Enter `source` path:\n>").replace('"', "")
    if not os.path.exists(source_path):
        while not os.path.exists(source_path):
            source_path = input(f"This path does not exists. Try again:\n>").replace('"', "")
    output_file = input(f"Enter `output` file:\n>").replace('"', "")
    if not os.path.exists(output_file):
        while not output_file.endswith(".txt"):
            output_file = input(f"This should be txt file. Try again:\n>").replace('"', "")
    
    Jadx = JadxToText(source_folder=source_path, output_file=output_file)
    Jadx.merge_source_to_txt()