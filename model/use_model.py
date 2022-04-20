import pickle

with open("prod_model.pkl", "rb") as m:
    model = pickle.loads(m.read())


model.predict([[299.3,310.6,1480.0,45.1,107,0,0,0,0,0,0]])