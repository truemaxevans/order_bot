from constants import Gender, ActivityLevel, Goal


class CaloriesCalculation:
    @staticmethod
    def calculate_bmr(weight, height, age, gender):
        if gender == Gender.MEN:
            return 10 * weight + 6.25 * height - 5 * age + 5
        elif gender == Gender.WOMAN:
            return 10 * weight + 6.25 * height - 5 * age - 161
        return 0

    @staticmethod
    def calculate_total_calories(bmr, activity_level):
        activity_multiplier = {
            ActivityLevel.MINIMUM: 1.2,
            ActivityLevel.THREE_TIMES_PER_WEEK: 1.375,
            ActivityLevel.FIVE_TIMES_PER_WEEK: 1.55,
            ActivityLevel.FIVE_TIMES_PER_WEEK_INTENSIVE: 1.725,
            ActivityLevel.TWO_TIMES_PER_DAY_OR_EVERYDAY_INTENSIVE: 1.9,
            ActivityLevel.EVERYDAY_AND_PHYSICAL_WORK: 2.1,
        }
        return bmr * activity_multiplier.get(activity_level, 1)

    @staticmethod
    def get_calorie_info(weight, height, age, gender, activity_level, goal):
        bmr = CaloriesCalculation.calculate_bmr(weight, height, age, gender)
        total_calories = CaloriesCalculation.calculate_total_calories(
            bmr, activity_level
        )

        if goal == Goal.WEIGHT_LOSS:
            total_calories -= 500
        elif goal == Goal.MUSCLE_GAIN:
            total_calories += 500

        protein = weight * 2
        fat = weight * 0.8
        carbs = (total_calories - protein * 4 - fat * 9) / 4

        return {
            "BMR": bmr,
            "Total Calories": total_calories,
            "Protein (grams)": protein,
            "Fat (grams)": fat,
            "Carbs (grams)": carbs,
        }
