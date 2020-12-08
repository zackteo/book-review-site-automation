#!/usr/bin/env python3

import math
import pyspark
from pyspark.sql import SparkSession
import pyspark.sql.functions as fnc
from pyspark.sql.functions import col

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

# drop unnecessary columns
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

# Getting average length. Use all reviews,
# Change null values to blank
reviews = (
    reviews.fillna("")
    .rdd.map(lambda x: (x.asin, len(x.reviewText.split(" "))))
    .toDF()
    .withColumnRenamed("_1", "asin_id")
    .withColumnRenamed("_2", "review_split")
    .groupby("asin_id")
    .agg(fnc.avg("review_split"))
)

# convert our metadata.csv into a dataframe
meta = (
    spark.read.format("json")
    .options(header="true", inferschema="true")
    .load(location + "meta_Kindle_Store.json")
)
meta.show(5)
meta = (
    meta.drop("description")
    .drop("imUrl")
    .drop("related")
    .drop("categories")
    .drop("title")
    .drop("salesRank")
    .dropna()
    .withColumn("price", col("price").cast("float"))
)

# ensure values are greater than 0
meta = meta.where((meta.price > 0))

combined_table = meta.join(reviews, meta.asin == reviews.asin_id)
combined_table = combined_table.drop("asin_id")
combined_table.show(5)

rdd = combined_table.rdd.map(list)
rdd.take(5)

# Pearson Correlation formula:
# total num terms = n
# sum of x = x_sum
# sum of y = y_sum
# sum of xy = xy_sum
# x squared sum = x_sq_sum
# y squared sum = y_sq_sum
# r = n(xy_sum) - (x_sum)(y_sum)/square_root( [n(x_sq_sum) - (x_sum)**2][n(y_sq_sum) - (y_sum)**2] )

# let x be price and y be average of review length

n = rdd.count()
x_sum = rdd.map(lambda x: x[1]).sum()
y_sum = rdd.map(lambda x: x[2]).sum()
xy_sum = rdd.map(lambda x: x[1] * x[2]).sum()
x_sq_sum = rdd.map(lambda x: x[1] ** 2).sum()
y_sq_sum = rdd.map(lambda x: x[2] ** 2).sum()

numerator = n * xy_sum - x_sum * y_sum
denominator = math.sqrt((n * x_sq_sum - (x_sum) ** 2) * (n * y_sq_sum - (y_sum) ** 2))

pearson = numerator / denominator
print("Pearson correlation coefficient: ", pearson)
