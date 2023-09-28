image_name = 'hello.hsjs.jpg'
current_user = 'bgakingo'

file_ext = image_name.rsplit('.', 1)[-1]

path = f'images/{current_user}.{file_ext}'

print(path)
