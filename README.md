# Book Review Website

Users can register for the website and then log in using their username and password. 
Once they log in, they will be able to search for books, leave reviews for individual books, and see the reviews made by other people.
Uses the API by Goodreads, another book review website, to pull in ratings from a broader audience. 
Users can query for book details and reviews programmatically via the website’s API.

This Python Flask web app uses a PostgreSQL database to keep track of books information, user information, and book reviews.  

Requirements

Registration: Users can register for the website, providing a username and password.

Login: Users, once registered, can log in to the website with their username and password.

Logout: Logged in users can log out of the site.

Import: A CSV of 5000 different books was imported. Each one has an ISBN number, a title, an author, and a publication year. The import.py program imports the books into the PostgreSQL database. 

Search: Once a user has logged in, they can search for a book. Users can type in the ISBN number of a book, the title of a book, or the author of a book. After performing the search, the website displays a list of possible matching results, or a message if there were no matches. If the user typed in only part of a title, ISBN, or author name, the search page finds matches for those as well!

Book Page: When users click on a book from the results of the search page, they are taken to a book page, with details about the book: its title, author, publication year, ISBN number, and any reviews that users have left for the book on the website.

Review Submission: On the book page, users can submit a review: consisting of a rating on a scale of 1 to 5, as well as a text component to the review where the user can write their opinion about a book. Users can't submit multiple reviews for the same book.

Goodreads Review Data: The book pages display (if available) the average rating and number of ratings the work has received from Goodreads.

API Access: If users make a GET request to the website’s /api/<isbn> route, where <isbn> is an ISBN number, the website returns a JSON response containing the book’s title, author, publication date, ISBN number, review count, and average score. The resulting JSON should follow the format:
{
    "title": "Memory",
    "author": "Doug Lloyd",
    "year": 2015,
    "isbn": "1632168146",
    "review_count": 28,
    "average_score": 5.0
}
If the requested ISBN number isn’t in the database, a 404 error is returned.

Note: Only raw SQL commands are used.

