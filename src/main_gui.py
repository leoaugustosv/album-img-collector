from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, Toplevel
from PIL import Image, ImageTk
import os, webbrowser
from io import BytesIO

from utils.libs.general import *
from utils.params.params import *
import utils.providers.soundcloud as sc
import utils.providers.youtube_music as ytm
import utils.libs.selenium as se


BROWSER = se.init_browser()

FETCHED_IMGS = []

def init_window():

    
    
    ### Layots
    def layout_no_path():
        frm_folder.grid(padx=10, pady=0, row=1)
        lbl_path.grid(pady=10, padx=0, row=1, column=0)
        btn_folder.grid(pady=0, padx=2, row=1, column=1)
        hr_quit.grid(padx=10, pady=5, row=2, sticky='ew')
        btn_quit.grid(pady=10, padx=50, row=3)

        grids_to_forget = [
            frm_files,
            frm_tags,
            frm_providers,
            btn_selectimg
        ]
        for grid in grids_to_forget:
            grid.grid_forget()



    def layout_has_path():
        frm_folder.grid(padx=10, pady=5, row=1)
        lbl_path.grid(pady=10, padx=0, row=1, column=0)
        btn_folder.grid(pady=0, padx=2, row=1, column=1)
        
        hr_img.grid(padx=10, pady=5, row=2, sticky='ew')


        frm_files.grid(padx=2, pady=0, row=4, column=0)
        lst_files.grid(padx=2, row=1, column=0)
        scrll_files.grid(row=1, rowspan=9, column=1)

        frm_providers.grid(padx=10, pady=2, row=5, column=0)
        frm_providers.grid_propagate(False)
        frm_providers.grid_columnconfigure(0, weight=1)
        frm_providers.grid_columnconfigure(1, weight=1)

        rdb_soundcloud.grid(sticky='ew', row=0, column=0)
        rdb_youtube.grid(sticky='ew', row=0, column=1)
        btn_search.grid(sticky="ew", padx=10, pady=5, row=1, column=0)
        btn_delcover.grid(sticky="ew", padx=10, pady=5, row=1, column=1)
        btn_selectimg.grid_forget()
        
        for btn in ACTION_BUTTONS:
            btn.config(state="disabled")

        frm_tags.grid(padx=10, pady=2, row=3, column=0)
        frm_tags.grid_propagate(False)
        frm_tags.grid_columnconfigure(0, weight=1)
        img_audio_tag.config(image=placeholder_tk)
        img_audio_tag.update()
        lbl_name_tag.config(text=f"Name: - ")
        lbl_artist_tag.config(text=f"Artist: - ")
        lbl_album_name_tag.config(text=f"Album Name: - ")
        img_audio_tag.grid(padx=2, pady= 0, row=0, column=0, sticky='ew')
        lbl_name_tag.grid(pady=2, padx=0, row=1, column=0, sticky='w')
        lbl_artist_tag.grid(pady=2, padx=0, row=2, column=0, sticky='w')
        lbl_album_name_tag.grid(pady=2, padx=0, row=3, column=0, sticky='w')
        

        hr_quit.grid(padx=10, pady=5, row=7, sticky='ew')
        btn_quit.grid(pady=10, padx=50, row=8)

    def update_layout(has_path=False):
        if has_path:
            layout_has_path()
        else: 
            lbl_path.config(text="Current path: None")
            layout_no_path()
        window.eval('tk::PlaceWindow . center')


    ### Commands
    def exit_window():
        window.quit()

    def open_link(event=None, url=None):
        if url:
            webbrowser.open(url)

    def set_folder_path():
        selected_path = filedialog.askdirectory(initialdir=os.getcwd())
        if selected_path:
            user_path.set(selected_path)
            has_path = True
            lst_files.delete(0, tk.END)
            audio_files_list = get_audio_files_from_path(user_path.get(), SUPPORTED_AUDIO_TYPES)

            if not audio_files_list:
                has_path = False
                update_layout(has_path)
                messagebox.showinfo(title = "Warning", message="No audio files found on selected path. Please select another folder.")
            else:
                lbl_path.config(text=user_path.get())
                for file in audio_files_list:
                    lst_files.insert(tk.END, file)
        else:
            has_path = False
        update_layout(has_path)

    def get_selected_file_name(event=None):
        selected_file_index = lst_files.curselection()
        if selected_file_index:
            selected_file = lst_files.get(selected_file_index[0])
        else:
            selected_file = ""
        return selected_file

    def show_file_id3_tags(event=None):
        for btn in ACTION_BUTTONS:
            btn.config(state="normal")

        selected_file = get_selected_file_name()
        
        if selected_file:
            name, artist, album_name, img_info, img_data = get_ID3_tags_info(os.path.join(user_path.get(), selected_file))
            print(
                f"FILE: {selected_file}\nNAME: {name}\nARTIST: {artist}\nALBUM: {album_name}\nIMG: {img_info}\n"
            )
            audio_name_tag.set(name)
            lbl_name_tag.config(text=f"Name: {audio_name_tag.get()}")

            audio_artist_tag.set(artist)
            lbl_artist_tag.config(text=f"Artist: {audio_artist_tag.get()}")

            audio_album_name_tag.set(album_name)
            lbl_album_name_tag.config(text=f"Album Name: {audio_album_name_tag.get()}")

            audio_img_info_tag.set(img_info)
            if not img_info:
                img_audio_tag.config(image=placeholder_tk)
                img_audio_tag.image = placeholder_tk
            else:
                bytes_to_img = Image.open(BytesIO(img_data))
                audio_img = ImageTk.PhotoImage(image=bytes_to_img.resize(TAG_IMG_PX_SIZE))
                img_audio_tag.config(image=audio_img)
                img_audio_tag.image = audio_img
                img_audio_tag.update()
    
    def search_provider(event=None):
        FETCHED_IMGS.clear()
        selected_provider_index = selected_provider.get()
        if selected_provider_index == 1:
            for img in sc.soundcloud_main(BROWSER, user_path.get(), get_selected_file_name()):
                FETCHED_IMGS.append(img)
        elif selected_provider_index == 2:
            for img in ytm.youtube_music_main(BROWSER, user_path.get(), get_selected_file_name()):
                FETCHED_IMGS.append(img)

        if FETCHED_IMGS:
            btn_selectimg.grid(sticky="ew", padx=10, pady=5, row=1, column=2)
            open_selection_window()
        else:
            btn_selectimg.grid_forget()
            messagebox.showinfo(title = "No image found", message="No image found for the selected audio file. Please select another provider and try again.")

    def open_selection_window(event=None):

        def enable_mouse_scroll(canvas):
            canvas.bind_all("<MouseWheel>", lambda event: canvas.yview_scroll(-int(event.delta / 120), "units"))

        def update_scroll_region(event):
            """Updates scroll region when resizing content."""
            canvas.configure(scrollregion=canvas.bbox("all"))

        # Top Window
        selection_window = Toplevel(window)
        selection_window.title("Select an Image")
        selection_window.grid_rowconfigure(0, weight=1)
        selection_window.grid_columnconfigure(0, weight=1)
        
        
        # Canvas
        canvas = tk.Canvas(selection_window, width=700, height=600)
        canvas.grid(row=0, column=0, sticky="nsew")

        scrollbar = tk.Scrollbar(selection_window, orient=tk.VERTICAL, command=canvas.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        canvas.configure(yscrollcommand=scrollbar.set)

        
        # Frame
        frm_imagelist = tk.Frame(canvas)
        frame_window = canvas.create_window((0, 0), window=frm_imagelist, anchor="nw")
        frm_imagelist.bind("<Configure>", update_scroll_region)
        enable_mouse_scroll(canvas)

        # List Images
        enumerated_imgs = enumerate(FETCHED_IMGS)
        for i, data in enumerated_imgs:
            label_info = f'{data.get("position")})\nUSER/ARTIST: {data.get("username")}\nTRACK NAME: {data.get("name")}'
            cover_url = data["cover_img"]
            track_url = data["url"]
            img = Image.open(response_to_img(cover_url)).resize((100, 100))
            img_tk = ImageTk.PhotoImage(img)

            lbl_imginfo = tk.Label(frm_imagelist, text=label_info)
            lbl_imginfo.grid(row=i*3, column=0, padx=0)

            lbl_tracklink = tk.Label(frm_imagelist, text=track_url, fg="blue", cursor="hand2")
            lbl_tracklink.bind("<Button-1>", lambda event,url=track_url:open_link(event,url))
            lbl_tracklink.grid(row=i*3+1, column=0, padx=0)

            btn = tk.Button(frm_imagelist, image=img_tk, command=lambda p=cover_url, topwindow=selection_window: select_image(p,topwindow))
            btn.image = img_tk
            btn.grid(row=i*3, column=1, padx=2)
            
    def select_image(image_url, top_window):
        audio_path = Path(user_path.get()).joinpath(get_selected_file_name())
        add_image_to_id3(image_url, audio_path)
        top_window.destroy()
        show_file_id3_tags()
        

    def clear_cover(event=None):
        selected_file = get_selected_file_name()
        answer = messagebox.askyesno("Clear Cover Art", f"Are you sure you want to clear the current cover art for \"{selected_file}\"?")
        if answer:
            try:
                delete_id3_cover(os.path.join(user_path.get(), selected_file))
                show_file_id3_tags()
            except Exception as e:
                print(f"FAIL: Unable to clear cover art - {e}")

    


    ### Frames config
    window = tk.Tk()
    window.title("Album IMG Collector V1")
    window.eval('tk::PlaceWindow . center')

    frm_folder = tk.Frame(window, relief=tk.SOLID)
    frm_files = tk.Frame(window, relief=tk.SOLID, width=80, height=6)
    frm_tags = tk.Frame(window, relief=tk.SOLID, width=500, height=300, bd=1)
    frm_providers = tk.Frame(window, relief=tk.SOLID, width=500, height=80)

    ### Global vars
    user_path = tk.StringVar(frm_tags, value=None)
    audio_name_tag = tk.StringVar(frm_tags, value=None)
    audio_artist_tag = tk.StringVar(frm_tags, value=None)
    audio_album_name_tag = tk.StringVar(frm_tags, value=None)
    audio_img_info_tag = tk.StringVar(frm_tags, value=None)
    selected_provider = tk.IntVar(value=1)

    ### Widgets
    lbl_path = tk.Label(frm_folder, text=f"Current path: None")
    img_folder = Image.open("src\\utils\\assets\\img\\folder-40.png")
    img_folder = ImageTk.PhotoImage(img_folder.resize((15,15)))
    btn_folder = tk.Button(frm_folder, image=img_folder, command=set_folder_path)
    

    hr_img = ttk.Separator(window, orient=tk.HORIZONTAL)
    hr_quit = ttk.Separator(window, orient=tk.HORIZONTAL)

    lst_files = tk.Listbox(frm_files, width=80, height=6)
    lst_files.bind("<<ListboxSelect>>", show_file_id3_tags)
    scrll_files = tk.Scrollbar(frm_files, orient=tk.VERTICAL, width=20)

    lst_files.config(yscrollcommand=scrll_files.set)
    scrll_files.config(command=lst_files.yview)

    placeholder_img = Image.open("src\\utils\\assets\\img\\placeholder.png")
    placeholder_tk = ImageTk.PhotoImage(image=placeholder_img.resize(TAG_IMG_PX_SIZE))
    img_audio_tag = tk.Label(frm_tags, anchor="center", justify="center", image=placeholder_tk)
    lbl_name_tag = tk.Label(frm_tags, anchor="w", justify="left", text=f"Name: - ")
    lbl_artist_tag = tk.Label(frm_tags, anchor="w", justify="left", text=f"Artist: - ")
    lbl_album_name_tag = tk.Label(frm_tags, anchor="w", justify="left", text=f"Album Name: - ")

    rdb_soundcloud = tk.Radiobutton(frm_providers, text="SoundCloud", variable=selected_provider, value=1)
    rdb_youtube = tk.Radiobutton(frm_providers, text="YouTube Music", variable=selected_provider, value=2)
    btn_search = tk.Button(frm_providers, text="Search Art", command=search_provider, state="disabled")
    btn_delcover = tk.Button(frm_providers, text="Clear Art", command=clear_cover, state="disabled")
    btn_selectimg = tk.Button(frm_providers, text="Change Art", command=open_selection_window)
    ACTION_BUTTONS = [btn_search, btn_delcover]

    btn_quit = tk.Button(window, text="Exit",  command=exit_window)
    update_layout()

    window.mainloop()




init_window()