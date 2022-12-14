import json
from flask import request, redirect, url_for, render_template, Blueprint, abort, Response   
from flaskr.file_system_helper import FileSystemHelper, FileSystemHelperResponse
from flaskr.file_system_helper import remove_file, check_file_is_existed, write_binary_to_file,\
        is_directory, give_relative_return_abs_path, check_post_is_allowed,get_binary_data_from_path
from flaskr import create_app
import base64

page = Blueprint('page', __name__, template_folder='templates')


@page.route('/root')
def page_root():
    return render_template("root.html")


@page.route('/')
def main_page():
    return redirect(url_for('page.page_root'))


@page.errorhandler(404)
def give_response_not_found():
    return {'Result':'Not Found'}, 404


@page.errorhandler(405)
def give_response_operation_not_allowed():
    return {'Result':'Operation Not Allowed'}, 405



def take_response(file_system_response):

    if file_system_response == FileSystemHelperResponse.NOT_FOUND:
        return give_response_not_found()
    elif file_system_response == FileSystemHelperResponse.OPERATION_NOT_ALLOWED:
        return give_response_operation_not_allowed()
    return {'Result':'Successful'}, 200


@page.route('/<path:localSystemFilePath>', methods=['GET'])
def get_resource(localSystemFilePath):
    file_path = give_relative_return_abs_path(localSystemFilePath)
    fs = FileSystemHelper()
    ret_source = []
    response = FileSystemHelperResponse.SUCCESS
    if not is_directory(file_path):
        response, ret_source = get_request_file(fs, file_path)
        if response == FileSystemHelperResponse.NOT_FOUND:
            return take_response(response)
        return ret_source
    else:
        response = fs.get_data_by_request(ret_source,
                                        file_path,
                                        request.args.get("orderBy"),
                                        request.args.get("orderByDirection"),
                                        request.args.get("filterByName"))
    if response == FileSystemHelperResponse.NOT_FOUND:
        return take_response(response)
    ret_data = fs.get_json_from_list(ret_source)
    return json.dumps(ret_data, indent=2)


def get_request_file(fs, file_path):
    if not check_file_is_existed(file_path):
        return FileSystemHelperResponse.NOT_FOUND, None
    if file_path.split('.')[-1] == 'png':
        return get_png_image(file_path)
    content = get_binary_data_from_path(file_path)
    return FileSystemHelperResponse.SUCCESS,content


def has_file_upload() -> bool:
    file = request.files.get('file', '')
    return file != ''


@page.route('/<path:localSystemFilePath>', methods=['POST'])
def page_post_request(localSystemFilePath):

    response = FileSystemHelperResponse.SUCCESS
    save_path = give_relative_return_abs_path(localSystemFilePath)
    # print(f'save_path: {save_path}, localSystemFilePath: {localSystemFilePath}')
    if check_post_is_allowed(save_path):
        if has_file_upload():
            file = request.files.get('file')
            binary_file = file.read()
        else:
            binary_file = request.get_data()
        response = write_binary_to_file(save_path, binary_file)
    else:
        response = FileSystemHelperResponse.OPERATION_NOT_ALLOWED

    return take_response(response)


@page.route('/<path:localSystemFilePath>', methods=['PATCH'])
def page_patch_request(localSystemFilePath):

    save_path = give_relative_return_abs_path(localSystemFilePath)

    if check_file_is_existed(save_path):
        if has_file_upload():
            file = request.files.get('file')
            binary_file = file.read()
        else:
            binary_file = request.get_data()
        response = write_binary_to_file(save_path, binary_file)
    else:
        response = FileSystemHelperResponse.OPERATION_NOT_ALLOWED

    return take_response(response)


@page.route('/<path:localSystemFilePath>', methods=['DELETE'])
def page_delete_request(localSystemFilePath):

    save_path = give_relative_return_abs_path(localSystemFilePath)
    response = FileSystemHelperResponse.NOT_FOUND

    if not check_file_is_existed(save_path):
        response = FileSystemHelperResponse.OPERATION_NOT_ALLOWED
    else:
        response = remove_file(save_path)
    return take_response(response)


def get_png_image(img_file_name):
    data = open(img_file_name, 'rb').read()
    image = base64.b64encode(data).decode()

    return render_template('show_png.html', image=image)


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
