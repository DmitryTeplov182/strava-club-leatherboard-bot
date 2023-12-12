import json
import config
from parse import StravaLeaderboardRetriever

def save_to_json_file(athletes_rank, club_id):
    """
    Сохраняет данные athletes_rank в файл JSON.

    :param athletes_rank: Данные для сохранения (словарь или список словарей).
    :param club_id: Идентификатор клуба для названия файла.
    """
    directory = './jsons'
    filename = f'{club_id}.json'
    filepath = f'{directory}/{filename}'

    with open(filepath, 'w', encoding='utf-8') as file:
        json.dump(athletes_rank, file, ensure_ascii=False, indent=4)

def main():
    """Main function"""

    # Get Athletes data
    strava = StravaLeaderboardRetriever(
        config.env.str("EMAIL"),
        config.env.str("PASSWD"),
        config.env.int("CLUB_ID"),
    )
    athletes_rank = strava.retrieve_leaderboard_data()
    
    # Сохраняем данные в файл JSON
    save_to_json_file(athletes_rank, config.env.int("CLUB_ID"))

if __name__ == "__main__":
    main()
