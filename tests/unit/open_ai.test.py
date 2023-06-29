import unittest

from movie_rec.openai_requestor import create_movie_list


# TODO Non Running Tests
class CreateMovieListTest(unittest.TestCase):
    def test_create_movie_list(self):
        response = """
        Sure, here are the top 10 psychological thrillers that will mess with your mind:
        
        1. Shutter Island, Year: 2010
        2. Inception, Year: 2010
        3. Memento, Year: 2000
        4. The Silence of the Lambs, Year: 1991
        5. Se7en, Year: 1995
        6. The Sixth Sense, Year: 1999
        7. The Prestige, Year: 2006
        8. Fight Club, Year: 1999
        9. Donnie Darko, Year: 2001
        10. Black Swan, Year: 2010
        """ # noqa
        expected_movie_data = [
            {"Index": "1", "Movie": "Shutter Island", "Year": "2010"},
            {"Index": "2", "Movie": "Inception", "Year": "2010"},
            {"Index": "3", "Movie": "Memento", "Year": "2000"},
            {"Index": "4", "Movie": "The Silence of the Lambs",
             "Year": "1991"},
            {"Index": "5", "Movie": "Se7en", "Year": "1995"},
            {"Index": "6", "Movie": "The Sixth Sense", "Year": "1999"},
            {"Index": "7", "Movie": "The Prestige", "Year": "2006"},
            {"Index": "8", "Movie": "Fight Club", "Year": "1999"},
            {"Index": "9", "Movie": "Donnie Darko", "Year": "2001"},
            {"Index": "10", "Movie": "Black Swan", "Year": "2010"}
        ]

        movie_data = create_movie_list(response)

        self.assertEqual(movie_data, expected_movie_data)


if __name__ == '__main__':
    unittest.main()
