import pywebio as io
import pywebio_battery as iob
import config
import os
import functools
from pywebio.platform.flask import webio_view
import flask

#########################################################################################################
#########################################################################################################

def bind_url_rule(path:str,endpoint:str,func,page_path:str):
    app.add_url_rule(
        rule=path, 
        endpoint='view_func_%s'%endpoint, 
        view_func=webio_view(functools.partial(func,page_path=page_path)), 
        methods=['GET', 'POST', 'OPTIONS']
    )

def redirect(url):
    io.output.put_html('<script type="text/javascript">window.location.href="%s";</script>'%url)

def put_blog(tag:str,blog_name:str):
    blog_name = blog_name[:len(blog_name)-3]
    blog_url = '%s/read?tag=%s&blog=%s'%(config.origin,tag,blog_name)
    io.output.put_markdown("> [%s](%s.md) "%(blog_name,blog_url))

def put_tag(tag_name:str):
    io.output.put_markdown('> [%s](%s/tags?tag=%s)'%(tag_name,config.origin,tag_name))

def put_find_msg(name:str,url:str):
    io.output.put_markdown('> %s: [%s](%s)'%(name,name,url))

#########################################################################################################
#########################################################################################################

app = flask.Flask(__name__)

#########################################################################################################
#########################################################################################################

def sidebar(page_path):
    io.output.put_row(
        [
            io.output.put_scope('sidebar'),
            None,
            io.output.put_scope('page')
        ],
        size='%s %s %s'%(config.sidebar,config.page_blank,config.page)
    )
    with io.output.use_scope('sidebar'):
        with open(config.image_dir_path+'logo.png','rb') as logo_img:
            io.output.put_row(
                [
                    io.output.put_image(logo_img.read(),width='100%',height='100%'),
                    None
                ],
                size='3fr 1fr'
            )
        io.output.put_markdown('# *Pages*')
        paths = config.url_rules.keys()
        for path in paths:
            if path not in config.excluded_paths:
                if path != page_path:
                    io.output.put_markdown('> [%s](%s%s)'%(config.url_rules[path][1],config.origin,path))
                else:
                    io.output.put_markdown('> %s'%config.url_rules[path][1])
        io.output.put_text('\n')
        io.output.put_markdown('# *%s* \n —— By %s'%(config.blog_name,config.developer))
        io.output.put_text('\n')
        io.output.put_markdown('# *Find Me On*')
        for msg in config.find_me:
            name = msg['name']
            url = msg['url']
            put_find_msg(name,url)
        io.output.put_text('\n')

def page_set(page_path):
    sidebar(page_path)
    io.config(
        theme=config.theme,
        title=config.blog_name
    )
    io.session.run_js('''
        var footer = document.getElementsByClassName('footer')[0];
        footer.parentNode.removeChild(footer);
    ''')
    io.session.set_env(output_max_width=config.max_width)

@app.errorhandler(404)
def Not_Found_Page(error):
    return '''
        <h1> %s Error </h1>
        <h3> 404 - Page Not Found </h3>
    '''%config.blog_name

def Admin(page_path):
    page_set(page_path)
    with io.output.use_scope('page'):
        if iob.get_cookie('is_admin_login') == 'true':
            io.output.put_row(
                [
                    None,
                    io.output.put_markdown('# %s Background'%config.blog_name),
                    None
                ],
                size='1fr 2fr 1fr'
            )
        else:
            redirect('%s/admin-login'%config.origin)

def Admin_login(page_path):
    page_set(page_path)
    with io.output.use_scope('page'):
        if iob.get_cookie('is_admin_login') != 'true':
            io.output.put_row(
                [
                    None,
                    io.output.put_markdown('# %s Admin Login'%config.blog_name),
                    None
                ],
                size='1fr 2fr 1fr'
            )
            io.pin.put_input('admin_name',type='text',label='Admin Name')
            io.pin.put_input('admin_password',type='password',label='Admin Password:')
            io.output.put_text('\n')
            def Admin_Login_Handle():
                admin_name = io.pin.pin.admin_name
                admin_password = io.pin.pin.admin_password
                if admin_name == config.admin_name and admin_password == config.admin_password:
                    iob.set_cookie('is_admin_login','true')
                    io.output.toast('登录成功',color='success')
                    redirect('%s/admin'%config.origin)
                else:
                    io.output.toast('登录失败',color='error')
            io.output.put_button('登录',onclick=Admin_Login_Handle)
        else:
            redirect('%s/admin'%config.origin)
        

def Tags(page_path):
    page_set(page_path)
    with io.output.use_scope('page'):
        query_string = iob.get_all_query()
        if 'tag' in query_string:
            io.output.put_markdown('> [返回](%s/tags)'%config.origin)
            io.output.put_text('\n')
            tags = os.listdir(config.blog_dir_path)
            tag = query_string['tag']
            if tag in tags and tag[0] != '.':
                blogs = os.listdir(config.blog_dir_path+tag+'/')
                for blog_name in blogs:
                    if blog_name[0] != '.':
                        put_blog(tag=tag,blog_name=blog_name)
            else:
                io.output.put_markdown('# 标签不存在')
        if 'tag' not in query_string:
            tags = os.listdir(config.blog_dir_path)
            def Search():
                io.output.clear('tags')
                with io.output.use_scope('tags'):
                    search_keyword = io.pin.pin.search_keyword
                    if search_keyword == '':
                        for tag in tags:
                            if tag[0] != '.':
                                put_tag(tag_name=tag)
                    else:
                        for tag in tags:
                            if tag[0] != '.':
                                if search_keyword.lower() in tag.lower():
                                    put_tag(tag_name=tag)
            io.output.put_row(
                [
                    io.pin.put_input('search_keyword'),
                    io.output.put_button('Search',onclick=Search),
                    None
                ]
            )
            io.output.put_text('\n')
            io.output.put_scope('tags')
            Search()

def Read(page_path):
    page_set(page_path)
    with io.output.use_scope('page'):
        query_string = iob.get_all_query()
        if 'tag' in query_string or 'blog' in query_string:
            tag = query_string['tag']
            blog_name = query_string['blog']
            blog_file_path = '%s/%s/%s'%(config.blog_dir_path,tag,blog_name)
            if os.path.isfile(blog_file_path):
                io.output.put_info(blog_name[:len(blog_name)-3])
                with open(blog_file_path,'r',encoding='utf-8') as blog_file:
                    io.output.put_markdown(blog_file.read())
            else:
                io.output.put_markdown('# 博客不存在')
        else:
            io.output.put_markdown('# 参数错误')

def About(page_path):
    page_set(page_path)
    with io.output.use_scope('page'):
        with open(config.image_dir_path+'python-logo.png','rb') as python_logo_img:
            io.output.put_image(python_logo_img.read(),width='50%')
        io.output.put_markdown('# *Powered by [Python](https://www.python.org/)*')
        io.output.put_text('\n')
        with open(config.image_dir_path+'flask-logo.png','rb') as flask_logo_img:
            io.output.put_image(flask_logo_img.read(),width='50%')
        io.output.put_markdown('# *Powered by [Flask](https://flask.palletsprojects.com/)*')
        io.output.put_text('\n')
        with open(config.image_dir_path+'pywebio-logo.png','rb') as pywebio_logo_img:
            io.output.put_image(pywebio_logo_img.read(),width='50%')
        io.output.put_markdown('# *Powered by [PyWebIO](https://www.pyweb.io/)*')
        io.output.put_text('\n')

def Index(page_path):
    page_set(page_path)
    with io.output.use_scope('page'):
        tags = os.listdir(config.blog_dir_path)
        def Search():
            io.output.clear('blogs')
            with io.output.use_scope('blogs'):
                search_keyword = io.pin.pin.search_keyword
                for tag in tags:
                    if tag[0] != '.':
                        blogs = os.listdir(config.blog_dir_path+tag+'/')
                        if search_keyword == '':
                            for blog_name in blogs:
                                if blog_name[0] != '.':
                                    put_blog(tag=tag,blog_name=blog_name)
                        else:
                            for blog_name in blogs:
                                if blog_name[0] != '.':
                                    if search_keyword.lower() in blog_name.lower():
                                        put_blog(tag=tag,blog_name=blog_name)
        io.output.put_row(
            [
                io.pin.put_input('search_keyword'),
                io.output.put_button('Search',onclick=Search),
                None
            ]
        )
        io.output.put_text('\n')
        io.output.put_scope('blogs')
        Search()

#########################################################################################################
#########################################################################################################

paths = config.url_rules.keys()
for path in paths:
    bind_url_rule(
        path=path,
        endpoint=config.url_rules[path],
        func=globals()[config.url_rules[path][0]],
        page_path=path
    )

app.run(host='0.0.0.0', port=8501,debug=True)