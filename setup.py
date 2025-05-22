from setuptools import setup, find_packages

setup(
    name="aisha_v2",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "aiogram>=3.0.0",
        "redis>=5.0.0",
        "pydantic>=2.0.0",
        "pydantic-settings>=2.0.0",
        "sqlalchemy>=2.0.0",
        "asyncpg>=0.27.0",
        "minio>=7.0.0",
        "aiohttp>=3.8.0",
    ],
    python_requires=">=3.9",
) 