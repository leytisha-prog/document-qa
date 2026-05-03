#import as panda to read the parquet files
import streamlit as st
import sklearn
import sklearn.metrics
import sklearn.linear_model
import sklearn.neural_network
import sklearn.feature_extraction.text
import pandas as pd

train_data = pd.read_parquet("/content/train-product-review.parquet")
test_data = pd.read_parquet("/content/test-product-review.parquet")

train_data.head()

#convert ratings into sentiment
def rating_to_sentiment(rating):
    if rating <= 2:
        return "negative"
    elif rating == 3:
        return "neutral"
    else:
        return "positive"
#change the 'stars' column into sentiment
train_data["sentiment"] = train_data["stars"].apply(rating_to_sentiment)
test_data["sentiment"] = test_data["stars"].apply(rating_to_sentiment)

X_train = train_data["review_body"]
y_train = train_data["sentiment"]
X_test = test_data["review_body"]
y_test = test_data["sentiment"]

#TF-IDF is applied to convert text into number by assinging value to the words according to their importance
from sklearn.feature_extraction.text import TfidfVectorizer

vectorizer = TfidfVectorizer()

X_train_vec = vectorizer.fit_transform(X_train)
X_test_vec = vectorizer.transform(X_test)

#model 1 training
from sklearn.linear_model import LogisticRegression
#trainingg the data with a max iteration of 1000 for proper convergence and improved performance
model1 = LogisticRegression(max_iter=1000)
model1.fit(X_train_vec, y_train)
#prediction/testing is done
pred1 = model1.predict(X_test_vec)

from sklearn.metrics import accuracy_score
#measure accuracy of the model as the evaluation metric
accuracy1 = accuracy_score(y_test, pred1)
print("Model 1 Accuracy:", accuracy1)

#model 2 training
from sklearn.neural_network import MLPClassifier
#used a max iteration of 300 due to execution time
model2 = MLPClassifier(max_iter=300)
model2.fit(X_train_vec, y_train)

pred2 = model2.predict(X_test_vec)

from sklearn.metrics import accuracy_score

accuracy2 = accuracy_score(y_test, pred2)
print("Model 2 Accuracy:", accuracy2)

#comparison of the models performances
print("Logistic Regression:", accuracy1)
print("MLP:", accuracy2)

#model 2 alternative training
from sklearn.neural_network import MLPClassifier
#added hidden layers revision for deep learning
model3 = MLPClassifier(max_iter=300, hidden_layer_sizes=(100,))
model3.fit(X_train_vec, y_train)

pred3 = model3.predict(X_test_vec)

from sklearn.metrics import accuracy_score

accuracy3 = accuracy_score(y_test, pred3)
print("Model 3 Accuracy:", accuracy3)

print("Logistic Regression:", accuracy1)
print("MLP1:", accuracy2)
print("MLP2:", accuracy3)

