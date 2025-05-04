
from database.db_manager import init_db
from ui_app.gui_main import launch_gui

if __name__ == "__main__":
    try:
        init_db()
        launch_gui()
    except Exception as e:
        print(f"[FATAL] 程序运行异常: {e}")
