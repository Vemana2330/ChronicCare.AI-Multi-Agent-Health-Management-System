from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.providers.snowflake.operators.snowflake import SnowflakeOperator
from datetime import datetime, timedelta
import sys
import os

# Ensure the /opt/airflow/recipe/ folder is in path for imports
sys.path.append('/opt/airflow')

# Import your extract function
from recipe.extract_recipe import extract_recipes_main

# Default DAG arguments
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2024, 1, 1),
    "email_on_failure": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

# Define the DAG
dag = DAG(
    dag_id="recipe_etl_dbt_pipeline",
    default_args=default_args,
    description="ETL pipeline: extract recipes → upload to S3 → load into Snowflake → run DBT transforms",
    schedule_interval=None,
    catchup=False,
)

# Task 1: Extract recipe data and upload to S3
extract_to_s3 = PythonOperator(
    task_id="extract_recipes_to_s3",
    python_callable=extract_recipes_main,
    dag=dag
)

# Task 2: Load from S3 to Snowflake with full SQL (with METADATA$FILENAME)
load_to_snowflake = SnowflakeOperator(
    task_id="load_s3_to_snowflake",
    snowflake_conn_id="snowflake_extract",  # Must match Airflow UI connection ID
    sql="""
        USE ROLE ACCOUNTADMIN;

        COPY INTO RECIPE_DB.RAW_DATA_SCHEMA.RAW_RECIPES
        FROM (
          SELECT
            REGEXP_REPLACE(METADATA$FILENAME, '.*\\/([^\\/]+)\\.csv', '\\\\1') AS recipe_name,
            $1 AS attribute,
            $2 AS value
          FROM @RECIPE_DB.RAW_DATA_SCHEMA.RECIPE_STAGE
        )
        FILE_FORMAT = RECIPE_DB.RAW_DATA_SCHEMA.CSV_FILE_FORMAT
        PATTERN = '.*\\.csv'
        ON_ERROR = CONTINUE;
    """,
    dag=dag
)

dbt_clean = BashOperator(
    task_id="dbt_clean",
    bash_command="cd /opt/airflow/dbt_recipe && dbt clean --profiles-dir .dbt",
    dag=dag
)

dbt_deps = BashOperator(
    task_id="dbt_deps",
    bash_command="cd /opt/airflow/dbt_recipe && dbt deps --profiles-dir .dbt",
    dag=dag
)

dbt_compile = BashOperator(
    task_id="dbt_compile",
    bash_command="cd /opt/airflow/dbt_recipe && dbt compile --profiles-dir .dbt",
    dag=dag
)

dbt_run = BashOperator(
    task_id="dbt_run",
    bash_command="cd /opt/airflow/dbt_recipe && dbt run --profiles-dir .dbt",
    dag=dag
)

dbt_test = BashOperator(
    task_id="dbt_test",
    bash_command="cd /opt/airflow/dbt_recipe && dbt test --profiles-dir .dbt",
    dag=dag
)

extract_to_s3 >> load_to_snowflake >> dbt_clean >> dbt_deps >> dbt_compile >> dbt_run >> dbt_test
