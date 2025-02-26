import streamlit as st
import preprocessor,helper
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
from fpdf import FPDF
import os
import matplotlib.font_manager as fm


st.set_page_config(
    page_title="Whatsapp-Chat-Analyser",
    page_icon="chat.png",
    layout="centered",
    initial_sidebar_state="expanded"  # Optional: can be "auto", "expanded", or "collapsed"
)

# Custom CSS
st.markdown(
    """
    <style>
        /* Main Background  */
        [data-testid="stAppViewContainer"], [data-testid="stApp"] {
            background-color: #000000 !important;
        }

        /* Change Sidebar Background (WhatsApp Green) */
        [data-testid="stSidebar"] {
            background-color: #075E54;
        }

        /* Remove Black Header Bar */
        header {
            background-color: #000000 !important;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# st.title("Welcome to WhatsApp Chat Analyzer")
st.sidebar.title("Whatsapp Chat Analyzer")

uploaded_file = st.sidebar.file_uploader("Choose a file")
if uploaded_file is not None:
    bytes_data = uploaded_file.getvalue()
    data = bytes_data.decode("utf-8")
    df = preprocessor.preprocess(data)

    # Fetch unique users
    user_list = df['user'].unique().tolist()
    user_list.remove('group_notification')  # Remove 'group_notification'
    user_list.sort()
    user_list.insert(0, "Overall")

    selected_user = st.sidebar.selectbox("Show analysis wrt", user_list)

    if st.sidebar.button("Show Analysis"):

        # Stats Area
        num_messages, words, num_media_messages, num_links = helper.fetch_stats(selected_user, df)
        st.title("Top Statistics")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown(
                "<div style='text-align: center;'><h4>Total Messages</h4><h2 style='color: #00FF00; margin-top: -10px;'>{}</h2></div>".format(
                    num_messages), unsafe_allow_html=True)

        with col2:
            st.markdown(
                "<div style='text-align: center;'><h4>Total Words</h4><h2 style='color: #00FF00; margin-top: -10px;'>{}</h2></div>".format(
                    words), unsafe_allow_html=True)

        with col3:
            st.markdown(
                "<div style='text-align: center;'><h4>Media Shared</h4><h2 style='color: #00FF00; margin-top: -10px;'>{}</h2></div>".format(
                    num_media_messages), unsafe_allow_html=True)

        with col4:
            st.markdown(
                "<div style='text-align: center;'><h4>Links Shared</h4><h2 style='color: #00FF00; margin-top: -10px;'>{}</h2></div>".format(
                    num_links), unsafe_allow_html=True)

        # Monthly timeline
        st.title("Monthly Timeline")
        timeline = helper.monthly_timeline(selected_user, df)
        fig, ax = plt.subplots()
        ax.plot(timeline['time'], timeline['message'], color='green')
        plt.xticks(rotation='vertical')
        st.pyplot(fig)

        # Daily timeline
        st.title("Daily Timeline")
        daily_timeline = helper.daily_timeline(selected_user, df)
        fig, ax = plt.subplots()
        ax.plot(daily_timeline['only_date'], daily_timeline['message'], color='black')
        plt.xticks(rotation='vertical')
        st.pyplot(fig)

        # Activity map
        st.title('Activity Map')
        col1, col2 = st.columns(2)

        with col1:
            st.header("Most busy day")
            busy_day = helper.week_activity_map(selected_user, df)
            fig, ax = plt.subplots()
            ax.bar(busy_day.index, busy_day.values, color='purple')
            plt.xticks(rotation='vertical')
            st.pyplot(fig)

        with col2:
            st.header("Most busy month")
            busy_month = helper.month_activity_map(selected_user, df)
            fig, ax = plt.subplots()
            ax.bar(busy_month.index, busy_month.values, color='orange')
            plt.xticks(rotation='vertical')
            st.pyplot(fig)

        st.title("Weekly Activity Map")
        user_heatmap = helper.activity_heatmap(selected_user, df)
        fig, ax = plt.subplots()
        ax = sns.heatmap(user_heatmap)
        st.pyplot(fig)

        # Finding the busiest users in the group (Group level)
        if selected_user == 'Overall':
            st.title('Most Busy Users')
            x, new_df = helper.most_busy_users(df)
            fig, ax = plt.subplots()

            col1, col2 = st.columns(2)

            with col1:
                ax.bar(x.index, x.values, color='red')
                plt.xticks(rotation='vertical')
                st.pyplot(fig)
            with col2:
                st.dataframe(new_df)

        # WordCloud
        st.title("Wordcloud")
        df_wc = helper.create_wordcloud(selected_user, df)
        fig, ax = plt.subplots()
        ax.imshow(df_wc)
        st.pyplot(fig)

        # Most common words
        most_common_df = helper.most_common_words(selected_user, df)

        fig, ax = plt.subplots()
        ax.barh(most_common_df[0], most_common_df[1])
        plt.xticks(rotation='vertical')
        st.title('Most common words')
        st.pyplot(fig)

         # Sentiment Analysis Results
        st.title("Sentiment Analysis")

        if selected_user == "Overall":
            st.write("Sentiment distribution across all users:")
            sentiment_counts = df["sentiment"].value_counts()
            st.bar_chart(sentiment_counts)
        else:
            st.write(f"Sentiment distribution for user: {selected_user}")
            df = df[df["user"] == selected_user]
            sentiment_counts = df["sentiment"].value_counts()
            st.bar_chart(sentiment_counts)

        # Sentiment Distribution by User
        if selected_user == 'Overall':
            st.write("Sentiment distribution for each user:")
            sentiment_by_user = df.groupby('user')['sentiment'].value_counts().unstack().fillna(0)
            st.write(sentiment_by_user)

            # Emoji analysis
            plt.rcParams["font.family"] = "Noto Color Emoji"

            emoji_df = helper.emoji_helper(selected_user, df)
            emoji_df = emoji_df[
                emoji_df[0] != "group_notification"
                ]  # Remove 'group_notification'
            st.title("Emoji Analysis")
            st.write("Emoji analysis by count")

            # Display emoji list
            # with st.expander("Emoji List"):
            # emoji_df.columns = ["Emoji", "Count"]
            st.dataframe(emoji_df)

            # Aggregate emojis by category or frequency
            aggregated_data = (
                emoji_df.groupby(0)[1].sum().nlargest(5)
            )  # Example: Top 10 most frequent emojis

            # Plot aggregated data using Plotly
            fig = go.Figure(
                data=[go.Bar(x=aggregated_data.index, y=aggregated_data.values)]
            )
            fig.update_layout(xaxis_title="Emoji", yaxis_title="Frequency")
            st.write("Emoji analysis by chart")
            st.plotly_chart(fig)


        # Word Frequency by User
        st.title("Word Frequency by User")
        if selected_user == 'Overall':
            st.write("Select a user to see their most frequent words.")
        else:
            word_freq_df = helper.word_frequency_by_user(selected_user, df)
            st.table(word_freq_df)

            # 📄 Generate and Download PDF Report at the end
            stats = {
                "Total Messages": num_messages,
                "Total Words": words,
                "Media Shared": num_media_messages,
                "Links Shared": num_links
            }

            pdf_file = preprocessor.generate_pdf(selected_user, stats, sentiment_counts, emoji_df)

            if os.path.exists(pdf_file):  # Ensure the file exists
                with open(pdf_file, "rb") as pdf:
                    st.download_button(
                        label="📄 Download Analysis Report",
                        data=pdf,
                        file_name="WhatsApp_Chat_Report.pdf",
                        mime="application/pdf"
                    )
            else:
                st.error("⚠️ Error generating the PDF report.")
