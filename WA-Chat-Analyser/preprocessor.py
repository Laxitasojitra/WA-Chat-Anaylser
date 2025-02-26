
import re
import pandas as pd
from textblob import TextBlob

def preprocess(data):
    pattern = r"\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2}\s-\s"

    messages = re.split(pattern, data)[1:]
    dates = re.findall(pattern, data)

    df = pd.DataFrame({'user_message': messages, 'message_date': dates})
    # convert message_date type
    df['message_date'] = pd.to_datetime(df['message_date'], format='%m/%d/%y, %H:%M - ')

    df.rename(columns={'message_date': 'date'}, inplace=True)

    users = []
    messages = []
    sentiments = []  # New list to store sentiment analysis results
    for message in df['user_message']:
        entry = re.split(r"([\w\W]+?):\s", message)
        if entry[1:]:  # user name
            users.append(entry[1])
            message_text = " ".join(entry[2:])
            messages.append(message_text)
            sentiment = analyze_sentiment(message_text)  # Perform sentiment analysis
            sentiments.append(sentiment)
        else:
            users.append('group_notification')
            messages.append(entry[0])
            sentiments.append('Neutral')  # Assuming neutral sentiment for non-user messages

    df['user'] = users
    df['message'] = messages
    df['sentiment'] = sentiments  # Add sentiment analysis results to DataFrame

    df.drop(columns=['user_message'], inplace=True)

    df['only_date'] = df['date'].dt.date
    df['year'] = df['date'].dt.year
    df['month_num'] = df['date'].dt.month
    df['month'] = df['date'].dt.month_name()
    df['day'] = df['date'].dt.day
    df['day_name'] = df['date'].dt.day_name()
    df['hour'] = df['date'].dt.hour
    df['minute'] = df['date'].dt.minute

    period = []
    for hour in df[['day_name', 'hour']]['hour']:
        if hour == 23:
            period.append(str(hour) + "-" + str('00'))
        elif hour == 0:
            period.append(str('00') + "-" + str(hour + 1))
        else:
            period.append(str(hour) + "-" + str(hour + 1))

    df['period'] = period

    return df

def analyze_sentiment(message):
    blob = TextBlob(message)
    sentiment_score = blob.sentiment.polarity
    if sentiment_score > 0:
        return "Positive"
    elif sentiment_score < 0:
        return "Negative"
    else:
        return "Neutral"


    #pdf
from fpdf import FPDF


def generate_pdf(selected_user, stats, sentiment_counts, emoji_df):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Title
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, "WhatsApp Chat Analysis Report", ln=True, align="C")
    pdf.ln(10)

    # User
    pdf.set_font("Arial", "B", 14)
    pdf.cell(200, 10, f"Analysis for: {selected_user}", ln=True, align="L")
    pdf.ln(5)

    # Stats
    pdf.set_font("Arial", size=12)
    for key, value in stats.items():
        pdf.cell(200, 10, f"{key}: {value}", ln=True)

    pdf.ln(10)

    # Sentiment Analysis
    pdf.set_font("Arial", "B", 14)
    pdf.cell(200, 10, "Sentiment Analysis", ln=True, align="L")
    pdf.ln(5)

    for sentiment, count in sentiment_counts.items():
        pdf.cell(200, 10, f"{sentiment}: {count}", ln=True)

    pdf.ln(10)

    # Emoji Analysis
    pdf.set_font("Arial", "B", 14)
    pdf.cell(200, 10, "Emoji Analysis", ln=True, align="L")
    pdf.ln(5)

    for index, row in emoji_df.iterrows():
        emoji, count = row[0], row[1]
        pdf.cell(200, 10, f"{emoji}: {count}", ln=True)

    # Save PDF file
    pdf_path = "WhatsApp_Chat_Report.pdf"
    pdf.output(pdf_path)
    return pdf_path