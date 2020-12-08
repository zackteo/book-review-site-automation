#!/usr/bin/env python3

import math
import pyspark
from pyspark.sql import SparkSession
import pyspark.sql.functions as fnc
from pyspark.sql.functions import col
from pyspark.sql.window import Window

sc = pyspark.SparkContext("local[*]")
spark = SparkSession(sc)

# get namenode dns url
fil = open("namenode_ip.txt", "r")
location = fil.read()
fil.close()

# get reviews from hdfs and load into dataframe
reviews = (
    spark.read.format("csv")
    .options(header="true", inferschema="true")
    .load(location + "kindle_reviews.csv")
)
# reviews.show(5)

reviews = (
    reviews.drop("_c0")
    .drop("helpful")
    .drop("overall")
    .drop("reviewTime")
    .drop("reviewerID")
    .drop("reviewerName")
    .drop("summary")
    .drop("unixReviewTime")
)
# reviews.show(5)

# split it into words
doc_and_words = (
    reviews.select(
        "asin", fnc.explode(fnc.split("reviewText", "[\W_]+")).alias("each_word")
    )
    .filter(fnc.length("each_word") > 0)
    .select("asin", fnc.trim(fnc.lower(fnc.col("each_word"))).alias("each_word"))
)


# tf = (num of term in doc)/(total num of words in doc)
wind = Window.partitionBy(doc_and_words["asin"])

tf = (
    doc_and_words.groupBy("asin", "each_word")
    .agg(
        fnc.count("*").alias("num_words"),
        fnc.sum(fnc.count("*")).over(wind).alias("num_docs"),
        (fnc.count("*") / fnc.sum(fnc.count("*")).over(wind)).alias("tf"),
    )
    .orderBy("num_words", ascending=False)
    .drop("num_words")
    .drop("num_docs")
)

tf.show(truncate=5)

# idf = (log((total num docs) / num of docs with term in it))
# asin -> document count
total_num_docs = doc_and_words.select("asin").distinct().count()

wind = Window.partitionBy("each_word")

idf = (
    doc_and_words.groupBy("each_word", "asin")
    .agg(
        fnc.lit(total_num_docs).alias("total_num_docs"),
        fnc.count("*").over(wind).alias("docs_with_term"),
        fnc.log(fnc.lit(total_num_docs) / fnc.count("*").over(wind)).alias("idf"),
    )
    .orderBy("idf", ascending=False)
    .drop("total_num_docs")
    .drop("doc_with_term")
)

idf.show(truncate=5)

# Combine both tables to calculate tfidf

tfidf = (
    tf.join(idf, ["asin", "each_word"])
    .withColumn("tfidf", fnc.col("tf") * fnc.col("idf"))
    .drop
)

tfidf.orderBy("tfidf", ascending=False).show(truncate=12)
