import os

# Папки, где нужны __init__.py
folders = [
    "app",
    "app/api",
    "app/api/endpoints",
    "app/core",
    "app/models",
    "app/services",
    "app/schemas",
    "app/utils"
]

for folder in folders:
    # Создаем папку если не существует
    os.makedirs(folder, exist_ok=True)

    # Создаем __init__.py
    init_file = os.path.join(folder, "__init__.py")
    if not os.path.exists(init_file):
        with open(init_file, 'w', encoding='utf-8') as f:
            f.write('')
        print(f"Создан: {init_file}")
    else:
        print(f"Уже существует: {init_file}")