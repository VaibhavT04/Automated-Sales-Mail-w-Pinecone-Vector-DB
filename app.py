from langchain_community.document_loaders import WebBaseLoader
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import streamlit as st
import os
import re

#for mail
import smtplib
from email.mime.text import MIMEText


st. set_page_config(page_title="Cold Mail Auto Generation", page_icon=":robot:")
st.title("Cold Mail Auto Generation with context")

link = st.text_input("Enter the job posting link:")
gmail_pass = st.text_input("Enter your Gmail App Password(16 characters):", type="password")
to_mail = st.text_input("Enter Email Recruiter Incharge:")

gmail_user = "vaibhavtatkare2004@gmail.com"

load_dotenv()
groq = os.getenv("GROQ")

# LLM
llm = ChatGroq(
    groq_api_key=groq,
    model="llama-3.1-8b-instant",
    temperature=0.7
)

def clean_text(text: str) -> str:
    # Replace newlines & tabs with space
    text = re.sub(r"[\n\t\r]+", " ", text)

    # Collapse multiple spaces into one
    text = re.sub(r"\s{2,}", " ", text)

    # Strip leading/trailing space
    return text.strip()


submit = st.button("Generate and Send Email")

if submit:
    if link:
        if gmail_pass:
            # Loader
            loader = WebBaseLoader(link)
            job_data = loader.load()

            title = job_data[0].metadata.get("title")
            description = job_data[0].metadata.get("description")
            content = clean_text(job_data[0].page_content)
            

            prompt_template = PromptTemplate.from_template(
                "You are helpful expert assistant, get the incharge of job posting of hiring team mention in this job postion content: {content}."
                "Provide the result in clean short JSON strict format"
            )
            parser = JsonOutputParser()

            chain = prompt_template | llm | parser
            res = chain.invoke({
                "content": content
            })

            prompt_t = PromptTemplate.from_template(
                """
            You are an expert career assistant.

            Generate a professional job application email **in JSON format** with exactly two keys:
            1. "subject" → short and professional subject line.
            2. "body" → email body text.

            Rules for the email body:
            - Structure the email in **4 paragraphs**, 1–2 lines per paragraph, with a line space between paragraphs.
            - Start with a greeting addressing the hiring manager's name from {res} (if unavailable, just use "Hey").
            - End with a professional closing (e.g., "Best regards, Vaibhav Tatkare").
            - Mention your **resume link** naturally: https://drive.google.com/file/d/1lzFyv7BKdrw7y0hx9Lobo1obLMPASaiu/view?usp=sharing
            - Mention your **GitHub link** naturally: https://github.com/VaibhavT04
            - Show your **knowledge of their company and the role**, emphasizing alignment and why you are best suited.
            - Keep it concise, professional, confident, and eager.
            - Candidate profile: 4th-year Computer Engineering student, CGPA 9.23, hands-on AI/ML and Full-Stack experience, production-ready projects on GitHub.
            - Do not exceed 120 words.
            - Output **only valid JSON**, no explanations, no markdown.

            Hiring Manager Info:
            {res}

            Job Details:
            {content}
            """
            )

            final_chain = prompt_t | llm | parser
            mail = final_chain.invoke({
                "res": res,
                "content": content
            })

            msg = MIMEText(mail['body'])
            msg['Subject'] = mail['subject']
            msg['From'] = gmail_user
            msg['To'] = to_mail

            # Send email
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(gmail_user, gmail_pass)
                server.send_message(msg)
                st.success("Cold mail generated and sent successfully!")

            print("Email sent successfully!")


        else:
            st.warning("Please provide valid Gmail App Pass")
    else:
        st.warning("Please provide a valid job posting link")
