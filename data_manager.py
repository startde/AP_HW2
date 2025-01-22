from utils import get_food_info
class DataManager:
    def __init__(self):
        """
        Инициализация менеджера данных без начального профиля
        """
        self.users = {}  # Словарь для хранения данных всех пользователей
        self.workout_calories = {
            "бег": 10,           # ккал в минуту
            "ходьба": 4,         
            "плавание": 8,       
            "велосипед": 7,      
            "йога": 3,           
            "силовая": 6,        
            "crossfit": 12,      
            "танцы": 5,          
            "футбол": 9,         
            "баскетбол": 8       
        }

    def create_profile(self, user_id: str, profile_data: dict):
        # Базовые расчеты на основе данных пользователя
        weight = float(profile_data['weight'])
        height = float(profile_data['height'])
        age = int(profile_data['age'])
        activity = int(profile_data['activity'])
        
        # Расчет BMR (базового метаболизма) по формуле Миффлина-Сан Жеора
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
        
        # Коэффициент активности
        activity_multiplier = self.get_activity_multiplier(activity)
        
        # Расчет дневной нормы калорий
        daily_calories = bmr * activity_multiplier
        
        # Расчет нормы воды (30 мл на кг веса)
        water_goal = weight * 30

        # Создание профиля пользователя
        self.users[user_id] = {
            "profile": {
                "weight": weight,
                "height": height,
                "age": age,
                "activity": activity,
                "city": profile_data['city'],
                "calorie_goal": round(daily_calories),
                "water_goal": round(water_goal)
            },
            "daily_logs": {
                "water": 0,
                "calories_in": 0,
                "calories_burned": 0,
                "food_log": [],
                "workout_log": []
            }
        }
        
        return self.users[user_id]["profile"]

    def get_activity_multiplier(self, activity_minutes: int) -> float:
        if activity_minutes < 30:
            return 1.2  # Сидячий образ жизни
        elif activity_minutes < 60:
            return 1.375  # Легкая активность
        elif activity_minutes < 120:
            return 1.55  # Умеренная активность
        elif activity_minutes < 180:
            return 1.725  # Высокая активность
        else:
            return 1.9  # Очень высокая активность

    def log_water(self, user_id: str, amount: float) -> dict:
        if user_id not in self.users:
            return {"error": "Профиль не найден"}
        
        self.users[user_id]["daily_logs"]["water"] += amount
        remaining = self.users[user_id]["profile"]["water_goal"] - self.users[user_id]["daily_logs"]["water"]
        
        return {
            "logged": amount,
            "total": self.users[user_id]["daily_logs"]["water"],
            "remaining": remaining,
            "goal": self.users[user_id]["profile"]["water_goal"]
        }

    async def log_food(self, user_id: str, food_name: str, amount: float) -> dict:
        if user_id not in self.users:
            return {"error": "Профиль не найден"}

        food_info = await get_food_info(food_name)
        
        if not food_info:
            return {"error": "Продукт не найден в базе данных"}
            
        calories = (food_info.calories * amount) / 100
        self.users[user_id]["daily_logs"]["calories_in"] += calories
        self.users[user_id]["daily_logs"]["food_log"].append({
            "food": food_info.product_name,
            "amount": amount,
            "calories": calories
        })
        
        return {
            "food": food_info.product_name,
            "calories_per_100g": food_info.calories,
            "amount": amount,
            "calories": calories,
            "total_calories": self.users[user_id]["daily_logs"]["calories_in"]
        }

    def get_progress(self, user_id: str) -> dict:
        if user_id not in self.users:
            return {"error": "Профиль не найден"}
            
        user = self.users[user_id]
        return {
            "water": {
                "consumed": user["daily_logs"]["water"],
                "goal": user["profile"]["water_goal"],
                "remaining": user["profile"]["water_goal"] - user["daily_logs"]["water"]
            },
            "calories": {
                "consumed": user["daily_logs"]["calories_in"],
                "burned": user["daily_logs"]["calories_burned"],
                "goal": user["profile"]["calorie_goal"],
                "remaining": user["profile"]["calorie_goal"] - (
                    user["daily_logs"]["calories_in"] - user["daily_logs"]["calories_burned"]
                )
            },
            "food_log": user["daily_logs"]["food_log"],
            "workout_log": user["daily_logs"]["workout_log"]
        }

    def reset_daily_logs(self, user_id: str):
        """
        Сброс дневной статистики пользователя
        """
        if user_id in self.users:
            self.users[user_id]["daily_logs"] = {
                "water": 0,
                "calories_in": 0,
                "calories_burned": 0,
                "food_log": [],
                "workout_log": []
            }
    def log_workout(self, user_id: str, workout_type: str, duration: int) -> dict:
        if user_id not in self.users:
            return {"error": "Профиль не найден"}

        workout_type = workout_type.lower()
        if workout_type not in self.workout_calories:
            return {
                "error": "Тип тренировки не найден",
                "available_types": list(self.workout_calories.keys())
            }

        # Расчет сожженных калорий
        calories_per_minute = self.workout_calories[workout_type]
        calories_burned = calories_per_minute * duration
        
        # Расчет рекомендуемого количества воды (200 мл за каждые 30 минут)
        water_recommendation = (duration // 30 + (1 if duration % 30 > 0 else 0)) * 200

        # Применяем коэффициент в зависимости от веса пользователя
        user_weight = self.users[user_id]["profile"]["weight"]
        weight_coefficient = user_weight / 70  # нормализация относительно веса 70 кг
        calories_burned = round(calories_burned * weight_coefficient)

        # Обновляем статистику пользователя
        self.users[user_id]["daily_logs"]["calories_burned"] += calories_burned
        self.users[user_id]["daily_logs"]["workout_log"].append({
            "type": workout_type,
            "duration": duration,
            "calories_burned": calories_burned,
            "water_recommendation": water_recommendation
        })

        # Получаем общий баланс калорий за день
        total_calories_in = self.users[user_id]["daily_logs"]["calories_in"]
        total_calories_burned = self.users[user_id]["daily_logs"]["calories_burned"]
        calories_balance = total_calories_in - total_calories_burned

        return {
            "workout_type": workout_type,
            "duration": duration,
            "calories_burned": calories_burned,
            "water_recommendation": water_recommendation,
            "daily_stats": {
                "total_calories_burned": total_calories_burned,
                "calories_consumed": total_calories_in,
                "calories_balance": calories_balance
            }
        }

    def get_available_workouts(self) -> list:
        """
        Получение списка доступных типов тренировок
        """
        return list(self.workout_calories.keys())