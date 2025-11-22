"""
Script para verificar se os produtos foram inseridos no banco de dados
"""
import pymysql

# RDS connection details (mesmas do Lambda)
host = 'padaria-db.cyzbfkdaor1i.us-east-1.rds.amazonaws.com'
user = "padaria_livia"
password = "P$dAr1$12345"
database = "padaria-db"

def verificar_produtos():
    """Verifica os produtos no banco de dados"""
    try:
        connection = pymysql.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )

        with connection.cursor() as cursor:
            # Conta quantos produtos existem
            cursor.execute("SELECT COUNT(*) FROM consumidor_item")
            total = cursor.fetchone()[0]
            print(f"✅ Total de produtos no banco: {total}")

            # Lista os produtos
            cursor.execute("SELECT id, nome, quantidade_estoque, disponivel FROM consumidor_item ORDER BY id")
            produtos = cursor.fetchall()

            print("\n📦 Produtos no banco de dados:")
            print("-" * 70)
            for produto in produtos:
                disponivel = "✅" if produto[3] else "❌"
                print(f"ID {produto[0]:2d} | {produto[1]:25s} | Estoque: {produto[2]:3d} | {disponivel}")

        connection.close()

    except Exception as e:
        print(f"❌ Erro ao conectar ao banco: {str(e)}")

if __name__ == "__main__":
    verificar_produtos()
