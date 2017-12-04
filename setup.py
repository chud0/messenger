from setuptools import setup, find_packages

setup(
    name="avacado_messenger",
    version='0.1.1',
    description='Server for short text messanger',
    url='https://github.com/chud0/messenger',
    author="chud0",
    author_email="www.chud0@mail.ru",
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 3.6',
    ],
    install_requires=["SQLAlchemy"],
    python_requires=">=3",
    # py_modules=["server", "jim"],
    packages=find_packages(),
    package_data={
        "server": ["server.sqlite"],
        "client": ["user.svg", "message.svg", "client.sqlite"]
    },
    entry_points={
        'console_scripts': [
            'server = server.server:mainloop',
        ],
        'gui_scripts': [
            'client = client.gui_app_client:main',
        ],
    },
)
