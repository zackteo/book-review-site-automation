(ns pearson.core
  (:require
   [clojure.pprint]
   [zero-one.geni.core :as g]
   [zero-one.geni.ml :as ml]
   [zero-one.geni.repl :as repl]
   [clojure.string :as str]
   [clojure.math.numeric-tower :as math])
  (:gen-class))

;; Realised that I didn't know how to set up clojure for the EC2 cluster

;; Correlation: compute the Pearson correlation between price and average review length.

(defonce spark (future (g/create-spark-session {})))
(defonce json-frame (g/read-json! "resources/meta_Kindle_Store.json"))
(defonce csv-frame (g/read-csv! "resources/kindle_reviews.csv"))


;; (-> json-frame (g/limit 5) g/show-vertical)
;; (g/print-schema json-frame)
;; (-> csv-frame (g/limit 5) g/show-vertical)
;; (g/print-schema csv-frame)


;; Inner join on book id
;; multiple instances of reviews?
(def kindle-unioned
  (-> (g/join json-frame csv-frame
              (g/=== (g/col json-frame :asin) (g/col csv-frame :asin)) "inner")))

;; (g/print-schema kindle-unioned)
;; root
;; |-- _corrupt_record: string (nullable = true)
;; |-- asin: string (nullable = true)
;; |-- brand: string (nullable = true)
;; |-- categories: array (nullable = true)
;; |    |-- element: array (containsNull = true)
;; |    |    |-- element: string (containsNull = true)
;; |-- description: string (nullable = true)
;; |-- imUrl: string (nullable = true)
;; |-- price: double (nullable = true)
;; |-- related: struct (nullable = true)
;; |    |-- also_bought: array (nullable = true)
;; |    |    |-- element: string (containsNull = true)
;; |    |-- also_viewed: array (nullable = true)
;; |    |    |-- element: string (containsNull = true)
;; |    |-- bought_together: array (nullable = true)
;; |    |    |-- element: string (containsNull = true)
;; |    |-- buy_after_viewing: array (nullable = true)
;; |    |    |-- element: string (containsNull = true)
;; |-- salesRank: struct (nullable = true)
;; |    |-- Cell Phones & Accessories: long (nullable = true)
;; |    |-- Clothing: long (nullable = true)
;; |-- title: string (nullable = true)
;; |-- _c0: string (nullable = true)
;; |-- asin: string (nullable = true)
;; |-- helpful: string (nullable = true)
;; |-- overall: integer (nullable = true)
;; |-- reviewText: string (nullable = true)
;; |-- reviewTime: string (nullable = true)
;; |-- reviewerID: string (nullable = true)
;; |-- reviewerName: string (nullable = true)
;; |-- summary: string (nullable = true)
;; |-- unixReviewTime: string (nullable = true)

;; possibly need to filter duplicate reviews/reviews by same reviewer
;; Should I split to account for it's and day-to-day? maybe comma too and full stop
(def relevant
  (-> kindle-unioned
      (g/select (g/col json-frame :asin)
                :title
                :price
                :reviewText
                (-> (g/size (g/split (g/col :reviewText) " "))
                    (g/as "reviewLength")))
      (g/filter (g/not-null? :reviewText))
      (g/filter (g/not-null? :price))))

;; (g/print-schema relevant)
;; root
;; |-- asin: string (nullable = true)
;; |-- title: string (nullable = true)
;; |-- price: double (nullable = true)
;; |-- reviewText: string (nullable = true)
;; |-- length(reviewText): integer (nullable = true)

;; Check
(-> relevant
    (g/group-by :asin :price)
    (g/agg {:avgReviewLength (g/mean :reviewLength)})
    (g/select :asin 
              :price
              :avgReviewLength)
    (g/select (g/corr :price :avgReviewLength))
    g/first)
;; => {:corr(price, avgReviewLength) 0.03828714598766705}
(-> relevant
    (g/group-by :asin :price)
    (g/agg {:avgReviewLength (g/mean :reviewLength)})
    (g/select :asin
              :price
              :avgReviewLength)
    (g/select {:n-rows                      (g/count "*")
               :total-price                 (g/sum :price)
               :total-avg-review-length     (g/sum :avgReviewLength)
               :total-???                   (g/sum (g/* :price :avgReviewLength))
               :total-sqrt-price            (g/sum (g/sqr :price))
               :total-sqr-avg-review-length (g/sum (g/sqr :avgReviewLength))})
    g/first)

(def my-vector [221364.0700000272 5787234.967057779 2.3438528029087618E7 4105045.0819000844 8.065201143575892E8 57156])

(let [[x y xy x2 y2 n] my-vector
      top              (- (* n xy) (* x y))
      bot-left         (- (* n x2) (math/expt x 2))
      bot-right        (- (* n y2) (math/expt y 2))
      r                (/ top (math/sqrt (* bot-left bot-right)))]
  r)

;; Stuffs

;; nzeed to figure this out
(def tfidf
  (-> kindle-unioned
      (g/select (g/col json-frame :asin)
                :reviewText
                ;; (-> (g/size (g/split (g/col :reviewText) " "))
                ;;     (g/as "reviewLength"))
                )
      (g/filter (g/not-null? :reviewText))
      ))

;; (-> tfidf
;;     (g/limit 100)
;;     (g/write-csv! "resources/kindle_reviews_new.csv"))


(defonce spark (future (g/create-spark-session {})))
(defonce tfidf (g/read-csv! "resources/kindle_reviews_new.csv"))

(def pipeline
  (ml/pipeline
    (ml/tokenizer {:input-col  :reviewText
                   :output-col :words})
    (ml/hashing-tf {:num-features 20
                    :input-col    :words
                    :output-col   :raw-features})
    (ml/idf {:input-col  :raw-features
             :output-col :features})
    ))


(def pipeline-model
  (ml/fit tfidf pipeline))


(def new-tfidf (-> tfidf
                   (g/group-by :asin)
                   (g/agg (g/concat :reviewText))
                   g/first))


(-> tfidf
    (ml/transform pipeline-model)
    (g/select :asin
              :words
              :raw-features
              :features)
    ;; (g/select {:tf    :raw-features
    ;;            :idf   :features
    ;;            :tfidf (g/* :tf :idf)})
    (g/limit 3)
    (g/show)
    )
;;+----------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
;;|asin      |words                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |raw-features                                                                                                                                 |features                                                                                                                                                                                                                                                                                                                                                                                                                                             |
;;+----------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
;;|B000FC26RI|[pat, anjali, is, the, da, man, of, an, overview, of, spiritual, practice,, from, an, indian, perspective, 600, ad., , (or, is, that, 800, ad?)the, most, controversial, part, of, pj,, imo,, is, he, discusses, at, length, the, siddhis, or, powers, accruing, from, sp.but, the, definition, of, sp,, according, to, pat, is, in, the, opening:yogaham, chitta, vritti, narodaham.yoga, is, the, stilling, of, the, thought, , waves, of, the, mind.orcloseness, to, god, is, a, result, of, clearing, out, childish, distractions, of, the, mind.a, must, have, book, on, every, learned, person's, book, shelf,, but, see, another, reviewer's, comments, on, the, translation, -, evidently, thekindle, is, crap,, or, scholarly, quality.so, -, buy, the, book,, and, avoid, the, kindle.]|(20,[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19],[4.0,6.0,4.0,5.0,2.0,5.0,2.0,5.0,4.0,14.0,8.0,3.0,7.0,3.0,5.0,12.0,3.0,14.0,1.0,6.0])|(20,[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19],[0.6898770414037719,2.3736768699909168,1.4097625591997764,0.4666596989610956,0.5168233803033355,0.9215185899897289,0.1650420473760069,0.576554232554972,0.596849592746703,1.7707780595276759,1.1022696189044237,0.3459325395329832,0.8071759255769607,0.5174077810528289,1.9050700612200004,1.5178097653094365,0.44763719456002726,1.4596541445417324,0.4254657748148339,1.9479664541572097])|
;;|B000FC26RI|[simply, stated, and, translated,, this, copy, is, easily, understood., the, review, says, it, has, to, have, eleven, more, words, to, be, accepted,, so, here, they, are.]                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |(20,[0,2,3,4,6,8,9,10,11,12,13,15,16,17,18,19],[2.0,2.0,1.0,1.0,2.0,3.0,2.0,1.0,1.0,1.0,1.0,3.0,2.0,1.0,2.0,1.0])                            |(20,[0,2,3,4,6,8,9,10,11,12,13,15,16,17,18,19],[0.34493852070188596,0.7048812795998882,0.09333193979221913,0.25841169015166776,0.1650420473760069,0.44763719456002726,0.2529682942182394,0.13778370236305296,0.1153108465109944,0.1153108465109944,0.17246926035094298,0.3794524413273591,0.2984247963733515,0.10426101032440946,0.8509315496296678,0.3246610756928683])                                                                             |
;;|B000FC26RI|[i, have, several, translations, of, the, yoga, sutras, and, did, find, this, one, a, fairly, understandable, one., it, has, a, decent, layout, and, you, can, move, through, it, fairly, fast.]                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |(20,[0,2,4,5,6,7,9,10,11,13,15,16,17,18,19],[1.0,3.0,1.0,1.0,4.0,3.0,1.0,1.0,3.0,3.0,2.0,1.0,1.0,3.0,2.0])                                   |(20,[0,2,4,5,6,7,9,10,11,13,15,16,17,18,19],[0.17246926035094298,1.0573219193998322,0.25841169015166776,0.1843037179979458,0.3300840947520138,0.3459325395329832,0.1264841471091197,0.13778370236305296,0.3459325395329832,0.5174077810528289,0.2529682942182394,0.14921239818667575,0.10426101032440946,1.2763973244445017,0.6493221513857366])                                                                                                     |
;;+----------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
;;
;;
;;nil
;;
;;
;;(g/print-schema (-> tfidf
;;                    (ml/transform pipeline-model)
;;                    ))
;;root
;;|-- asin: string (nullable = true)
;;|-- reviewText: string (nullable = true)
;;|-- words: array (nullable = true)
;;|    |-- element: string (containsNull = true)
;;|-- raw-features: vector (nullable = true)
;;|-- features: vector (nullable = true)
;;
;;
;;nil
;;
;;(def sentence-data
;;  (g/table->dataset
;;    [[0.0 "Hi I heard about Spark"]
;;     [0.0 "I wish Java could use case classes"]
;;     [1.0 "Logistic regression models are neat"]]
;;    [:label :sentence]))
;;
;;
;;
;;
;;(def pipeline
;;  (ml/pipeline
;;    (ml/tokenizer {:input-col  :sentence
;;                   :output-col :words})
;;    (ml/hashing-tf {:num-features 20
;;                    :input-col    :words
;;                    :output-col   :raw-features})
;;    (ml/idf {:input-col  :raw-features
;;             :output-col :features})))
;;
;;
;;(def pipeline-model
;;  (ml/fit sentence-data pipeline))
;;
;;(-> sentence-data
;;    (ml/transform pipeline-model)
;;    (g/collect-col :features))
;;
;;
