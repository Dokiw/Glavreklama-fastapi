import click
from app.db.migrations import create_migration, upgrade_database, create_initial_migration

@click.group()
async def cli():
    """CLI для управления базой данных"""
    pass

@cli.command()
@click.option('--message', '-m', default='auto migration', help='Сообщение миграции')
async def migrate(message):
    """Создает новую миграцию"""
    create_migration(message)

@cli.command()
@click.option('--revision', '-r', default='head', help='Ревизия для применения')
async def upgrade(revision):
    """Применяет миграции"""
    upgrade_database(revision)

@cli.command()
async def init():
    """Создает начальную миграцию"""
    create_initial_migration()

if __name__ == '__main__':
    cli()
