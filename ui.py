import os
import os.path
import platform
import json

if platform.system() == 'Windows':
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(2)

import dearpygui.dearpygui as dpg
from dearpygui_ext.themes import create_theme_imgui_light, create_theme_imgui_dark

import command_combiner

dpg.create_context()
dpg.create_viewport(title='Minecraft command combiner', width=1200, height=600)
dpg.setup_dearpygui()

def on_viewport_resize():
    dpg.set_item_height("#mainwindow", dpg.get_viewport_height())
    dpg.set_item_width("#mainwindow", dpg.get_viewport_width())
    dpg.set_item_pos("#mainwindow", (0, 0))

with dpg.font_registry():
    if platform.system() == 'Windows':
        fontPath = os.path.join(os.getenv('WINDIR'), 'Fonts', 'SegUIVar.ttf')
        if os.path.exists(fontPath) and os.path.isfile(fontPath):
            dpg.bind_font(dpg.add_font(fontPath, 20))

theme = True

def set_theme(dark: bool):
    global theme
    
    if dark:
        dark_theme = create_theme_imgui_dark()
        dpg.bind_theme(dark_theme)
    else:
        light_theme = create_theme_imgui_light()
        dpg.bind_theme(light_theme)
    
    theme = dark

set_theme(True)

def show_info(title, message):
    with dpg.window(label=title, modal=True, no_close=True) as modal_id:
        dpg.add_text(message)
        with dpg.group(horizontal=True):
            dpg.add_button(label="Close", width=75, user_data=(modal_id, True), callback=lambda: dpg.delete_item(modal_id))
    dpg.split_frame()
    centerOnScreen(modal_id)

def centerOnScreen(element):
    viewport_width = dpg.get_viewport_client_width()
    viewport_height = dpg.get_viewport_client_height()
    width = dpg.get_item_width(element)
    height = dpg.get_item_height(element)
    dpg.set_item_pos(element, [viewport_width // 2 - width // 2, viewport_height // 2 - height // 2])

commands = []
commandElements = []

def command_update_callback(elementID):
    commands[commandElements.index(elementID)] = dpg.get_value(dpg.get_item_children(dpg.get_item_children(elementID)[1][0])[1][0])

def insertCommand():
    if len(commands) == 0:
        dpg.delete_item("#commands", children_only=True)
    commands.append("")
    with dpg.table(header_row=False, parent="#commands") as table:
        commandElements.append(table)
        dpg.add_table_column()
        dpg.add_table_column(width_fixed=True)
        with dpg.table_row():
            dpg.add_input_text(callback=lambda: command_update_callback(table), width=-1)
            dpg.add_button(label="...", callback=lambda: showCommandActions(table))

def showCommandActions(table):
    with dpg.window(label="Actions", modal=True, no_resize=True) as window:
        dpg.add_menu_item(label="Move up", callback=lambda: moveUp(commandElements.index(table)))
        dpg.add_menu_item(label="Move down", callback=lambda: moveDown(commandElements.index(table)))
        dpg.add_menu_item(label="Insert above", callback=lambda: insertAbove(commandElements.index(table)))
        dpg.add_menu_item(label="Insert below", callback=lambda: insertBelow(commandElements.index(table)))
        dpg.add_menu_item(label="Remove", callback=lambda: removeCommand(commandElements.index(table)))
        dpg.add_menu_item(label="Cancel", callback=lambda: dpg.delete_item(window))
    dpg.split_frame()
    centerOnScreen(window)

def insertBelow(index):
    insertCommand()
    newCommandIndex = len(commands) - 1
    if index < newCommandIndex - 1:
        dpg.move_item(commandElements[newCommandIndex], before=commandElements[index + 1])
        commands.insert(index + 1, commands[newCommandIndex])
        commandElements.insert(index + 1, commandElements[newCommandIndex])
        commands.pop()
        commandElements.pop()

def insertAbove(index):
    insertBelow(index)
    moveDown(index)

def removeCommand(index):
    del commands[index]
    dpg.delete_item(commandElements[index])
    del commandElements[index]
    
    if len(commands) == 0:
        dpg.add_text("(No commands added yet)", parent="#commands")

def moveUp(index):
    if index < 1:
        show_info("Can't move up", "This command is already at the top.")
        return
    previousIndex = index - 1
    dpg.move_item(commandElements[index], parent="#commands", before=commandElements[previousIndex])
    commands[previousIndex], commands[index] = commands[index], commands[previousIndex]
    commandElements[previousIndex], commandElements[index] = commandElements[index], commandElements[previousIndex]

def moveDown(index):
    if index + 1 >= len(commands):
        show_info("Can't move up", "This command is already at the top.")
        return
    nextIndex = index + 1
    dpg.move_item(commandElements[nextIndex], parent="#commands", before=commandElements[index])
    commands[nextIndex], commands[index] = commands[index], commands[nextIndex]
    commandElements[nextIndex], commandElements[index] = commandElements[index], commandElements[nextIndex]

def export(file: str, mode: command_combiner.CombineMode):
    if mode == -2:
        with dpg.window(modal=True, no_close=True, label="Importing...") as importModal:
            dpg.add_text("Importing, please wait...")
        dpg.split_frame()
        try:
            with open(file, 'r') as f:
                lines = f.readlines()
            while len(commands) > 0:
                removeCommand(0)
            for line in lines:
                line = line.strip().strip('\n')
                insertCommand()
                dpg.set_value(dpg.get_item_children(dpg.get_item_children(commandElements[-1])[1][0])[1][0], line)
                commands[-1] = line
            dpg.delete_item(importModal)
            dpg.split_frame()
            show_info("Import finished.", "The import has been finished.")
        except:
            dpg.delete_item(importModal)
            dpg.split_frame()
            show_info("Import failed.", "Something went wrong during the import.")
            raise
        return
            
    
    if len(commands) == 0:
        show_info("Nothing to export", "You didn't add any commands.")
        return
    with dpg.window(modal=True, no_close=True, label="Exporting...") as exportModal:
        dpg.add_text("Exporting, please wait...")
    dpg.split_frame()
    centerOnScreen(exportModal)
    try:
        if type(mode) == int and mode >= 0 or type(mode) == command_combiner.CombineMode:
            result = command_combiner.combine_commands(commands, mode)
        elif type(mode) == int and mode == -1:
            result = "\n".join(commands)
        with open(file, 'w') as f:
            if type(result) != str:
                result = json.dumps(result)
            f.write(result)
        dpg.delete_item(exportModal)
        dpg.split_frame()
        show_info("Export finished.", "The export has been finished.")
    except Exception:
        dpg.delete_item(exportModal)
        dpg.split_frame()
        show_info("Export failed.", "Something went wrong during the export.")
        raise

def on_save_clicked(file: str, mode: command_combiner.CombineMode):
    dpg.split_frame()
    if os.path.exists(file) and mode != -2:
        if not os.path.isfile(file):
            show_info("Not a file", "The path you selected already exists, but isn't a file.")
            return
        with dpg.window(label="Overwrite file?", modal=True, no_close=True) as dialog:
            dpg.add_text("You are about to overwrite a file.")
            dpg.add_text(file, bullet=True)
            dpg.add_text("Are you sure? All data stored in the file will be lost!")
            with dpg.table(header_row=False):
                dpg.add_table_column(width_fixed=True)
                dpg.add_table_column()
                dpg.add_table_column(width_fixed=True)
                
                with dpg.table_row():
                    def _overwrite_file_on_click():
                        dpg.delete_item(dialog)
                        dpg.split_frame()
                        export(file, mode)
                    dpg.add_button(label="Overwrite file", callback=_overwrite_file_on_click)
                    dpg.add_spacer()
                    dpg.add_button(label="Cancel", callback=lambda: dpg.delete_item(dialog))
        dpg.split_frame()
        centerOnScreen(dialog)
        return
    if mode == -2:
        if not os.path.exists(file) or not os.path.isfile(file):
            show_info("File doesn't exist", "The file you selected doesn't exist, or it isn't a file.")
            return
    dpg.split_frame()
    export(file, mode)

def on_export_clicked(mode: command_combiner.CombineMode):
    with dpg.file_dialog(label="Select file", directory_selector=False, modal=True, width=dpg.get_viewport_width() / 2, height=dpg.get_viewport_height() / 2, callback=lambda _, data: on_save_clicked(data['file_path_name'], mode)) as file_dialog:
        dpg.add_file_extension(".txt", color=(0, 255, 0, 255), label="Text files (.txt)")
        dpg.add_file_extension("", color=(150, 255, 150, 128))
    dpg.bind_item_font(dpg.last_root(), '#segoeui')

def remove_empty_elements():
    with dpg.mutex():
        i = 0
        filteredCommands = []
        for command in commands:
            if command != "":
                filteredCommands.append(command)
        filteredCommandElements = []
        while len(commands) > 0:
            removeCommand(0)
        for command in filteredCommands:
            insertCommand()
            commands[-1] = command
            dpg.set_value(dpg.get_item_children(dpg.get_item_children(commandElements[-1])[1][0])[1][0], command)

with dpg.window(tag="#mainwindow", label="Command combiner", no_close=True, no_bring_to_front_on_focus=True, no_title_bar=True, no_resize=True, no_move=True, menubar=True):
    with dpg.menu_bar():
        with dpg.menu(label="Window"):
            dpg.add_checkbox(label="Dark theme", default_value=theme, callback=lambda: set_theme(not theme))
            dpg.add_menu_item(label="Close", callback=dpg.stop_dearpygui)
        with dpg.menu(label="Utilities"):
            dpg.add_menu_item(label="Remove empty elements", callback=remove_empty_elements)
            dpg.add_menu_item(label="Save commands", callback=lambda: on_export_clicked(-1))
            dpg.add_menu_item(label="Load commands", callback=lambda: on_export_clicked(-2))
        with dpg.menu(label="Export"):
            dpg.add_menu_item(label="Export as entity NBT", callback=lambda: on_export_clicked(command_combiner.CombineMode.ENTITY_NBT))
            dpg.add_menu_item(label="Export as summon command", callback=lambda: on_export_clicked(command_combiner.CombineMode.SUMMON_CMD))
            dpg.add_menu_item(label="Export as spawn egg item NBT", callback=lambda: on_export_clicked(command_combiner.CombineMode.SPAWN_EGG_NBT))
            dpg.add_menu_item(label="Export as spawn egg give command", callback=lambda: on_export_clicked(command_combiner.CombineMode.GIVE_CMD_SPAWN_EGG))
    dpg.add_text("Combine multiple commands into a single one.")
    dpg.add_text("When exporting as a command block or a spawn egg, the commands are ran 2 blocks above the command block.", bullet=True)
    dpg.add_text("When exporting as a summon command, the commands run 1 block higher than the place where the falling block lands.", bullet=True)
    dpg.add_text("Avoid adding more than 50 commands, as it may not work due to the Minecraft chunk entity limit.", bullet=True)
    with dpg.menu(label="Add new command..."):
        dpg.add_menu_item(label="... to the bottom (F2)", callback=insertCommand)
        dpg.add_menu_item(label="... to the top (F3)", callback=lambda: insertBelow(-1))
    with dpg.child_window(tag="#commands"):
        dpg.add_text("(No commands added yet)")

dpg.set_viewport_resize_callback(on_viewport_resize)
dpg.set_primary_window("#mainwindow", True)

with dpg.handler_registry():
    dpg.add_key_press_handler(dpg.mvKey_F2, callback=insertCommand)
    dpg.add_key_press_handler(dpg.mvKey_F3, callback=lambda: insertBelow(-1))

dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()