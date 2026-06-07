import pyodbc
import pandas as pd
import streamlit as st
# Veritabanı bağlantısını sağlayan fonksiyon
def get_connection():
    try:

        conn_str = (
            r'DRIVER={SQL Server};'
            r'SERVER=.\SQLEXPRESS;'
            r'DATABASE=AkademikDanismanlikDB;'
            r'Trusted_Connection=yes;'
        )
        conn = pyodbc.connect(conn_str)
        return conn
    except Exception as e:
        st.error(f"Veritabanı bağlantı hatası: {e}")
        return None

# SQL'den veri okuyup Pandas DataFrame'e çeviren yardımcı fonksiyon
def fetch_query(query, params=None):
    conn = get_connection()
    if conn:
        if params:
            df = pd.read_sql(query, conn, params=params)
        else:
            df = pd.read_sql(query, conn)
        conn.close()
        return df
    return pd.DataFrame()

# SQL'e veri ekleme/güncelleme/silme yapan yardımcı fonksiyon
def execute_query(query, params=None):
    conn = get_connection()
    if conn:
        cursor = conn.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            conn.commit()
            return True
        except Exception as e:
            st.error(f"SQL Çalıştırma Hatası: {e}")
            return False
        finally:
            conn.close()
    return False