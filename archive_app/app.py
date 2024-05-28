from flask import Flask, request, render_template, send_file, redirect, url_for
from werkzeug.utils import secure_filename
import os
import zipfile
import tarfile
from collections import defaultdict

app = Flask(__name__)  # Создание объекта Flask

# Конфигурация папок для загрузки файлов и скачивания архивов
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['DOWNLOAD_FOLDER'] = 'static/downloads/'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit
app.config['ALLOWED_EXTENSIONS'] = {'zip', 'tar'}  # Разрешенные расширения файлов
MAX_FILES_PER_IP = 5  # Максимальное количество файлов для загрузки с одного IP

files_counter = defaultdict(int)  # Счетчик загруженных файлов для каждого IP

def allowed_file(filename):
    """Проверка, допустимо ли расширение файла."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() not in app.config['ALLOWED_EXTENSIONS']

def create_zip(files, output_filename):
    """Создание ZIP-архива."""
    with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED, allowZip64=True) as zipf:
        # Создание архива и добавление файлов
        for file in files:
            arcname = os.path.basename(file)  # Получение только имени файла без пути
            zipf.write(file, arcname, compress_type=zipfile.ZIP_DEFLATED)  # Добавление файла в архив

def create_tar(files, output_filename):
    """Создание TAR-архива."""
    with tarfile.open(output_filename, 'w') as tarf:
        # Создание архива и добавление файлов
        for file in files:
            arcname = os.path.basename(file)  # Получение только имени файла без пути
            tarf.add(file, arcname=arcname)  # Добавление файла в архив

@app.route('/', methods=['GET', 'POST'])
def index():
    """Обработчик главной страницы."""
    if request.method == 'POST':
        ip_address = request.remote_addr  # Получение IP адреса пользователя
        if files_counter[ip_address] > MAX_FILES_PER_IP:
            return "Вы превысили максимальное количество файлов:" + str(MAX_FILES_PER_IP), 403  # Слишком много загруженных файлов

        if 'files' not in request.files:
            return redirect(request.url)  # Перенаправление на текущую страницу, если нет файлов для загрузки

        files = request.files.getlist('files')  # Получение списка загруженных файлов
        archive_format = request.form['format']  # Формат архива

        if archive_format not in app.config['ALLOWED_EXTENSIONS']:
            return "Недопустимый формат архива", 400  # Недопустимый формат архива

        filenames = []  # Список имен загруженных файлов
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)  # Безопасное имя файла
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)  # Путь для сохранения файла
                file.save(file_path)  # Сохранение файла на сервере
                filenames.append(file_path)  # Добавление пути файла в список

        output_filename = os.path.join(app.config['DOWNLOAD_FOLDER'], f'archive.{archive_format}')  # Путь для архива

        # Создание архива
        if archive_format == 'zip':
            create_zip(filenames, output_filename)  # Создание ZIP-архива
        elif archive_format == 'tar':
            create_tar(filenames, output_filename)  # Создание TAR-архива

        files_counter[ip_address] += len(filenames)  # Увеличение счетчика загруженных файлов

        return redirect(url_for('download_page', filename=f'archive.{archive_format}'))  # Перенаправление на страницу загрузки архива

    return render_template('index.html')  # Отображение главной страницы

@app.route('/download/<filename>')
def download_file(filename):
    """Обработчик скачивания архива."""
    return send_file(os.path.join(app.config['DOWNLOAD_FOLDER'], filename), as_attachment=True)  # Отправка файла на скачивание

@app.route('/download_page/<filename>')
def download_page(filename):
    """Обработчик страницы загрузки архива."""
    return render_template('download.html', filename=filename)  # Отображение страницы загрузки архива

if __name__ == '__main__':
    # Проверка существования папок для загрузки и скачивания файлов
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    if not os.path.exists(app.config['DOWNLOAD_FOLDER']):
        os.makedirs(app.config['DOWNLOAD_FOLDER'])
    app.run(debug=True)  # Запуск веб-приложения в режиме отладки
