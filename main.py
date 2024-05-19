import re
from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import JSONResponse
import MySQL_operate

app = FastAPI()

inprogress_orders = {}   # 存储订单会话ID(关于每个用户的)信息
# ”“”
# inprogress_orders结构：
# {
#     session_id1:{food1:number1,food2:number2,food3:number3},
#     session_id2:{foodx:number,foody:number}
# }
# “”“

@app.post("/")
async def handle_request(request: Request):
    # 捕获来自request的json数据
    payload = await request.json()

    intent = payload['queryResult']['intent']['displayName']
    parameters = payload['queryResult']['parameters']
    output_context = payload['queryResult']['outputContexts']

    session_id = extract_session_id(output_context[0]['name'])

    intent_handle_dict = {
        "order.add-context:ongoing-order": add_to_order,
        "order.remove-context:ongoing-order": remove_from_order,
        "order.complete-context:ongoing-order": complete_order,
        "track.order-context:ongoing-tracking": track_order
    }    # if intent == :
    #     # return JSONResponse(content={
    #     #     "fulfillmentText": f"Receive=={intent}==in backend",
    #     # })
    #     response = track_order(parameters)
    #     return response
    # elif intent == :
    # elif intent == "order.complete-context:ongoing-order":
    # elif intent == "order.complete-context:ongoing-order":

    return intent_handle_dict[intent](parameters, session_id)

def extract_session_id(session_str: str):
    match = re.search(r"/sessions/(.*?)/contexts/", session_str)
    return match.group(1) if match else ""

def get_food_from_dict(food_dict:dict):
    """
    从会话order中提取食物，以供删除功能使用
    """
    return ", ".join([f"{int(value)} {key}" for key,value in food_dict.items()])

def save_to_db(order: dict):
    """
    将本次会话的条目插入至数据库
    """
    next_order_id = MySQL_operate.get_next_order_id(order)

    for food_item,quantity in order.items():
        record = MySQL_operate.insert_order_item(
            food_item,
            quantity,
            next_order_id
        )
        if record == -1:
            return -1
    # 添加此order的状态信息
    MySQL_operate.insert_order_tracking(next_order_id, "in progress")

    return next_order_id

def add_to_order(parameters: dict, session_id: str):
    """
    将order内容添加至缓冲区
    """
    food_items = parameters["food-item"]
    quantities = parameters["number"]

    if len(food_items) != len(quantities):
        fulfillment_text = "Specify the foods  and numbers combined with them"
    else:
        new_food_dict = dict(zip(food_items,quantities))
        # 如果在当前会话记录中有该次session id，则追加order内容，否则新建session 点单实例
        if session_id in inprogress_orders:
            update_food_dict = inprogress_orders[session_id]
            update_food_dict.update(new_food_dict)
            inprogress_orders[session_id] = update_food_dict

        else:
            inprogress_orders[session_id] = new_food_dict

        order_strFormat = get_food_from_dict(inprogress_orders[session_id])
        fulfillment_text = f"{order_strFormat} you have ordered.Anything else?"

    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })

def remove_from_order(parameters: dict,session_id: str):
    """
    删除缓冲区中的order内容
    """
    fulfillment_text = ""
    if session_id not in inprogress_orders:
        fulfillment_text = "Apologise for you haven't order yet."
    else:
        food_items = parameters["food-item"]
        current_order = inprogress_orders[session_id]
        removed_items = []   #用于删除数据库记录
        no_such_items = []   #用于反馈用户错误

        for food_item in food_items:
            if food_item not in current_order:
                no_such_items.append(food_item)
                # fulfillment_text = "Apologise for you haven't order these."
            else:
                # 删除键值对
                removed_items.append(food_item)
                del current_order[food_item]
    if len(removed_items) > 0:
        fulfillment_text += f'Having removed {", ".join(removed_items)}from your order.'
    if len(no_such_items) > 0:
        fulfillment_text += f'But {", ".join(no_such_items)} is not in your order.'
    if len(current_order) == 0:
        fulfillment_text += f'Your order is now empty.'
    else:
        current_order_strFormat = get_food_from_dict(current_order)
        fulfillment_text += f'Here is what is left in your order: {current_order_strFormat}'

    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })

def complete_order(parameters: dict, session_id:str):
    if session_id not in inprogress_orders:
        fulfillment_text = "You have not ordered anything yet."
    else:
        session_order = inprogress_orders[session_id]
        order_id = save_to_db(session_order)
        if order_id == -1:
            fulfillment_text = "Failed to save your order. Please try again or wait moments."
        else:
            order_total = MySQL_operate.get_total_order_price(order_id)
            fulfillment_text = f"Your order has been placed. Your order id is {order_id}."\
                               f"Total price is {order_total},Thank you for your order!"
        # 完成此次会话后，删除缓冲区对应内存。order实例已经存储到MySQL中
        del inprogress_orders[session_id]
        return JSONResponse(content={
            "fulfillmentText": fulfillment_text
        })
def track_order(parameters: dict, session_id: str):
    # 获取order id
    order_id = int(parameters['order_id'])
    # 检索数据库
    order_status = MySQL_operate.get_order_status(order_id)
    if order_status:
        fulfillment_text = f"The status of order {order_id} is: {order_status}."
    else:
        fulfillment_text = f"Order not found: {order_id}."

    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })