import asyncio
import aiohttp
from pydantic.dataclasses import dataclass

@dataclass
class FoodInfo:
    product_name: str
    calories: float = 0

async def get_food_info(product_name: str) -> FoodInfo | None:

    url = f"https://world.openfoodfacts.org/cgi/search.pl?action=process&search_terms={product_name}&json=true"

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=30) as response:
                if response.status == 200:
                    data = await response.json()
                    products = data.get("products", [])
                    if products:  # Проверяем, есть ли найденные продукты
                        chosen_product = products[0]
                        for product in products:
                            if product.get("nutriments", {}).get("energy-kcal_100g", 0) != 0:
                                chosen_product = product
                                break
                        return FoodInfo(
                            product_name=chosen_product.get("product_name", "Неизвестно"),
                            calories=chosen_product.get("nutriments", {}).get("energy-kcal_100g", 0),
                        )
                    return None
                else:
                    print(f"Ошибка API: {response.status}, {await response.text()}")
        except aiohttp.ClientError as e:
            print(f"Ошибка клиента API: {e}")
        except asyncio.TimeoutError:
            print("Ошибка: Таймаут при запросе к API")
    return None