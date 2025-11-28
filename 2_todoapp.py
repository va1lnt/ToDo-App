import customtkinter as ctk
from tkinter import messagebox
import json
import os
from datetime import datetime


class TodoApp:
    def __init__(self):
        # Настройка внешнего вида
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Создание главного окна
        self.root = ctk.CTk()
        self.root.title("Планер для моей Мусеньки")
        self.root.geometry("600x700")
        self.root.resizable(True, True)

        # Переменные
        self.tasks = []
        self.data_file = "todo_data.json"
        self.expanded_tasks = set()  # Для отслеживания раскрытых задач

        # Загрузка данных
        self.load_data()

        # Создание интерфейса
        self.create_widgets()

    def create_widgets(self):
        # Заголовок
        self.title_label = ctk.CTkLabel(
            self.root,
            text="Список Дел моей Кошечки",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.title_label.pack(pady=20)

        # Фрейм для ввода новой задачи
        self.input_frame = ctk.CTkFrame(self.root)
        self.input_frame.pack(pady=10, padx=20, fill="x")

        self.task_entry = ctk.CTkEntry(
            self.input_frame,
            placeholder_text="Введите новую задачу...",
            font=ctk.CTkFont(size=14)
        )
        self.task_entry.pack(side="left", padx=10, pady=10, fill="x", expand=True)

        self.add_button = ctk.CTkButton(
            self.input_frame,
            text="Добавить",
            command=self.add_task,
            width=80
        )
        self.add_button.pack(side="right", padx=10, pady=10)

        # Привязка Enter к добавлению задачи
        self.task_entry.bind("<Return>", lambda event: self.add_task())

        # Фрейм для списка задач
        self.tasks_frame = ctk.CTkFrame(self.root)
        self.tasks_frame.pack(pady=10, padx=20, fill="both", expand=True)

        # Заголовок списка
        self.tasks_label = ctk.CTkLabel(
            self.tasks_frame,
            text="Список задач:",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.tasks_label.pack(pady=5)

        # Scrollable frame для задач
        self.scrollable_frame = ctk.CTkScrollableFrame(
            self.tasks_frame,
            height=400
        )
        self.scrollable_frame.pack(pady=10, padx=10, fill="both", expand=True)

        # Фрейм для кнопок управления
        self.control_frame = ctk.CTkFrame(self.root)
        self.control_frame.pack(pady=10, padx=20, fill="x")

        self.clear_completed_button = ctk.CTkButton(
            self.control_frame,
            text="Удалить выполненные",
            command=self.clear_completed,
            fg_color="#d9534f",
            hover_color="#c9302c"
        )
        self.clear_completed_button.pack(side="left", padx=5)

        self.clear_all_button = ctk.CTkButton(
            self.control_frame,
            text="Удалить все",
            command=self.clear_all,
            fg_color="#d9534f",
            hover_color="#c9302c"
        )
        self.clear_all_button.pack(side="left", padx=5)

        self.save_button = ctk.CTkButton(
            self.control_frame,
            text="Сохранить",
            command=self.save_data,
            fg_color="#5cb85c",
            hover_color="#4cae4c"
        )
        self.save_button.pack(side="right", padx=5)

        # Обновление отображения задач
        self.update_tasks_display()

    def add_task(self, parent_id=None, subtask_text=None):
        if subtask_text:
            task_text = subtask_text
        else:
            task_text = self.task_entry.get().strip()

        if task_text:
            task = {
                "id": len(self.tasks),
                "text": task_text,
                "completed": False,
                "parent_id": parent_id,
                "subtasks": [],
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "expanded": False
            }

            if parent_id is not None:
                # Добавляем подзадачу
                parent_task = self.find_task_by_id(parent_id)
                if parent_task:
                    subtask_id = f"{parent_id}_{len(parent_task['subtasks'])}"
                    task["id"] = subtask_id
                    parent_task["subtasks"].append(task)
            else:
                # Добавляем основную задачу
                self.tasks.append(task)

            if not subtask_text:
                self.task_entry.delete(0, 'end')

            self.update_tasks_display()
            self.save_data()
        else:
            if not subtask_text:
                messagebox.showwarning("Предупреждение", "Пожалуйста, введите текст задачи!")

    def find_task_by_id(self, task_id):
        """Рекурсивный поиск задачи по ID"""
        for task in self.tasks:
            if str(task["id"]) == str(task_id):
                return task
            # Ищем в подзадачах
            found = self.find_subtask_by_id(task["subtasks"], task_id)
            if found:
                return found
        return None

    def find_subtask_by_id(self, subtasks, task_id):
        """Поиск подзадачи по ID"""
        for subtask in subtasks:
            if str(subtask["id"]) == str(task_id):
                return subtask
            # Рекурсивный поиск вглубь
            found = self.find_subtask_by_id(subtask["subtasks"], task_id)
            if found:
                return found
        return None

    def toggle_task(self, task_id):
        task = self.find_task_by_id(task_id)
        if task:
            task["completed"] = not task["completed"]
            # Если задача завершена, завершаем все подзадачи
            if task["completed"]:
                self.complete_all_subtasks(task["subtasks"])
            self.update_tasks_display()
            self.save_data()

    def complete_all_subtasks(self, subtasks):
        """Рекурсивно завершает все подзадачи"""
        for subtask in subtasks:
            subtask["completed"] = True
            self.complete_all_subtasks(subtask["subtasks"])

    def toggle_expand(self, task_id):
        task = self.find_task_by_id(task_id)
        if task:
            task["expanded"] = not task["expanded"]
            self.update_tasks_display()
            self.save_data()

    def delete_task(self, task_id):
        """Удаление задачи и всех её подзадач"""
        if messagebox.askyesno("Подтверждение", "Удалить эту задачу и все подзадачи?"):
            # Удаляем из основного списка
            self.tasks = [task for task in self.tasks if str(task["id"]) != str(task_id)]

            # Рекурсивно удаляем из подзадач
            for task in self.tasks:
                self.remove_subtask(task, task_id)

            self.update_tasks_display()
            self.save_data()

    def remove_subtask(self, parent_task, task_id_to_remove):
        """Рекурсивно удаляет подзадачу"""
        parent_task["subtasks"] = [
            subtask for subtask in parent_task["subtasks"]
            if str(subtask["id"]) != str(task_id_to_remove)
        ]

        # Рекурсивно проверяем оставшиеся подзадачи
        for subtask in parent_task["subtasks"]:
            self.remove_subtask(subtask, task_id_to_remove)

    def add_subtask_dialog(self, parent_id):
        """Диалог для добавления подзадачи"""
        dialog = ctk.CTkInputDialog(
            text="Введите подзадачу:",
            title="Добавить подзадачу"
        )
        subtask_text = dialog.get_input()

        if subtask_text and subtask_text.strip():
            self.add_task(parent_id, subtask_text.strip())

    def clear_completed(self):
        if self.has_completed_tasks(self.tasks):
            self.tasks = [task for task in self.tasks if not self.is_task_completed(task)]
            self.update_tasks_display()
            self.save_data()
        else:
            messagebox.showinfo("Информация", "Нет выполненных задач для удаления!")

    def is_task_completed(self, task):
        """Проверяет, завершена ли задача и все её подзадачи"""
        if not task["completed"]:
            return False
        return all(self.is_task_completed(subtask) for subtask in task["subtasks"])

    def has_completed_tasks(self, tasks):
        """Проверяет, есть ли завершенные задачи"""
        return any(self.is_task_completed(task) for task in tasks)

    def clear_all(self):
        if self.tasks:
            if messagebox.askyesno("Подтверждение", "Вы уверены, что хотите удалить все задачи?"):
                self.tasks = []
                self.update_tasks_display()
                self.save_data()
        else:
            messagebox.showinfo("Информация", "Список задач пуст!")

    def update_tasks_display(self):
        # Очистка scrollable frame
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        # Отображение задач
        self.display_tasks_recursive(self.tasks)

    def display_tasks_recursive(self, tasks, level=0):
        """Рекурсивно отображает задачи и подзадачи"""
        for task in tasks:
            self.create_task_widget(task, level)

            # Отображаем подзадачи если задача раскрыта
            if task["expanded"] and task["subtasks"]:
                self.display_tasks_recursive(task["subtasks"], level + 1)

    def create_task_widget(self, task, level):
        """Создает виджет для одной задачи"""
        task_frame = ctk.CTkFrame(self.scrollable_frame, height=35)  # Фиксированная высота
        task_frame.pack(fill="x", pady=1, padx=5)
        task_frame.pack_propagate(False)  # Запрещаем изменение размера

        # Основной горизонтальный фрейм для содержимого
        content_frame = ctk.CTkFrame(task_frame, fg_color="transparent")
        content_frame.pack(fill="x", padx=5, pady=2)

        # Отступ для вложенности
        if level > 0:
            indent_label = ctk.CTkLabel(
                content_frame,
                text="  " * level,
                width=level * 10,
                fg_color="transparent"
            )
            indent_label.pack(side="left")

        # Кнопка раскрытия/скрытия подзадач
        if task["subtasks"]:
            expand_text = "▼" if task["expanded"] else "►"
            expand_button = ctk.CTkButton(
                content_frame,
                text=expand_text,
                width=20,
                height=20,
                fg_color="transparent",
                hover_color="#444444",
                font=ctk.CTkFont(size=10),
                command=lambda tid=task["id"]: self.toggle_expand(tid)
            )
            expand_button.pack(side="left", padx=(0, 5))
        else:
            # Заполнитель для выравнивания
            spacer = ctk.CTkLabel(content_frame, text="", width=25)
            spacer.pack(side="left", padx=(0, 5))

        # Чекбокс для отметки выполнения
        checkbox = ctk.CTkCheckBox(
            content_frame,
            text="",
            width=25,
            height=25,
            command=lambda tid=task["id"]: self.toggle_task(tid)
        )
        if task["completed"]:
            checkbox.select()
        checkbox.pack(side="left", padx=(0, 5))

        # Текст задачи
        task_text = task["text"]
        if task["completed"]:
            task_text = f"✓ {task_text}"

        task_label = ctk.CTkLabel(
            content_frame,
            text=task_text,
            font=ctk.CTkFont(size=13 if level > 0 else 14),
            anchor="w"
        )
        if task["completed"]:
            task_label.configure(text_color="gray")

        task_label.pack(side="left", padx=(0, 10), fill="x", expand=True)

        # Правая часть с кнопками
        right_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        right_frame.pack(side="right")

        # Индикатор подзадач
        if task["subtasks"]:
            completed_count = sum(1 for subtask in task["subtasks"] if subtask["completed"])
            subtask_indicator = ctk.CTkLabel(
                right_frame,
                text=f"{completed_count}/{len(task['subtasks'])}",
                font=ctk.CTkFont(size=10),
                text_color="#5bc0de"
            )
            subtask_indicator.pack(side="left", padx=5)

        # Кнопка добавления подзадачи
        if level < 3:  # Ограничиваем уровень вложенности
            add_subtask_button = ctk.CTkButton(
                right_frame,
                text="+",
                width=25,
                height=25,
                fg_color="#5bc0de",
                hover_color="#46b8da",
                font=ctk.CTkFont(size=12, weight="bold"),
                command=lambda tid=task["id"]: self.add_subtask_dialog(tid)
            )
            add_subtask_button.pack(side="left", padx=2)

        # Кнопка удаления
        delete_button = ctk.CTkButton(
            right_frame,
            text="×",
            width=25,
            height=25,
            fg_color="#d9534f",
            hover_color="#c9302c",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=lambda tid=task["id"]: self.delete_task(tid)
        )
        delete_button.pack(side="left", padx=2)

    def save_data(self):
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.tasks, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить данные: {str(e)}")

    def load_data(self):
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self.tasks = json.load(f)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить данные: {str(e)}")
            self.tasks = []

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = TodoApp()
    app.run()