import mysql.connector
global mydb

# 连接到MySQL数据库
mydb = mysql.connector.connect(
  host = "",
  user = "root",
  password = "123456",
  database = "pandeyji_eatery"
)

def get_order_status(order_id: int):
    """
    describe:获取订单状态
    order_id:订单编号
    """
    cursor = mydb.cursor()
    query = ("SELECT status FROM order_tracking WHERE order_id = %s")
    # 执行SELECT指令
    cursor.execute(query,(order_id,))
    result = cursor.fetchone()

    cursor.clo
    # mydb.close()

    return result[0] if result is not None else None

def get_next_id(order: dict):
    cursor = mydb.cursor()

    query = ("SELECT MAX(order_id) FROM orders")
    cursor.execute(query)

    result = cursor.fetchone()[0]

    cursor.close()

    if result is None:
        return 1
    else:
        return result + 1  #生成下一条order id

def insert_order_item(food_item: str, quantity: int, order_id: int):
    try:
        cursor = mydb.cursor()
        cursor.callproc('insert_order_item', (food_item, quantity, order_id))
        mydb.commit()
        cursor.close()
        print("food item 插入成功")
        return 1
    except mysql.connector.Error as err:
        print(f"插入失败: {err}")
        mydb.rollback()
        return -1
    except Exception as e:
        print(f"发生错误: {e}")
        mydb.rollback()
        return -1

def get_total_order_price(order_id: int):
    cursor = mydb.cursor()

    query = f"SELECT get_total_order_price({order_id})"  #调用数据库中函数
    cursor.execute(query)

    result = cursor.fetchone()[0]

    cursor.close()

    return result

def insert_order_tracking(order_id: int, status: str):
    cursor = mydb.cursor()

    query = "INSERT INTO order_tracking(order_id, status) VALUES (%s, %s)"
    cursor.execute(query, (order_id, status))
    mydb.commit()
    cursor.close()

