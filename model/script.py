
import sys
from collections import Counter
from contextlib import contextmanager
from datetime import datetime

import dataiku
import dataiku.core.pandasutils as pdu
import pickle
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

dataiku.set_remote_dss(
    "https://dss-d773f8f3-b079aed7-dku.eu-west-3.app.dataiku.io", "VzCQ4SocfPt6L96n3VsSuB4TS1SkpUyN")
dataiku.set_default_project_key("MAINPROJECT")

pd.options.mode.chained_assignment = None


def datetime_to_epoch(dt: datetime):
    return dt.timestamp()


def coerce_to_unicode(x):
    if sys.version_info < (3, 0):
        if isinstance(x, str):
            return unicode(x, 'utf-8')
        else:
            return unicode(x)
    else:
        return str(x)


@contextmanager
def track_elapsed_time(process_name: str):
    started_at = datetime.now()
    print(f"{process_name} process started at {started_at:%H:%M:%S}")

    try:
        yield

    except KeyboardInterrupt:
        print("Manually interrupted")

    finally:
        ended_at = datetime.now()
        print(
            f"{process_name} process finished at {ended_at:%H:%M:%S}"
            f" (elapsed: {ended_at - started_at})"
        )


# IMPORTING BASE DATA
preparation_steps = [{'type': 'ColumnsSelector', 'params': {'keep': False, 'appliesTo': 'COLUMNS', 'columns': [
    'product_id', 'udi']}, 'metaType': 'PROCESSOR', 'preview': True, 'disabled': False, 'alwaysShowComment': False}]

preparation_output_schema = {'columns': [{'name': 'type', 'type': 'string'}, {'name': 'air_temperature_k', 'type': 'double'}, {'name': 'process_temperature_k', 'type': 'double'}, {'name': 'rotational_speed_rpm', 'type': 'double'}, {
    'name': 'torque_nm', 'type': 'double'}, {'name': 'tool_wear_min', 'type': 'bigint'}, {'name': 'machine_failure', 'type': 'boolean'}, {'name': 'twf', 'type': 'boolean'}, {'name': 'hdf', 'type': 'boolean'}, {'name': 'pwf', 'type': 'boolean'}, {'name': 'osf', 'type': 'boolean'}, {'name': 'rnf', 'type': 'boolean'}], 'userModified': False}

ml_dataset_handle = dataiku.Dataset("sensor_data")

ml_dataset_handle.set_preparation_steps(
    preparation_steps, preparation_output_schema
)

with track_elapsed_time("PREPARATION STEP"):
    ml_dataset = ml_dataset_handle.get_dataframe()

print('Base data has %i rows and %i columns' %
      (ml_dataset.shape[0], ml_dataset.shape[1]))

categorical_features = ['twf', 'osf', 'hdf', 'rnf', 'type', 'pwf']
numerical_features = ['rotational_speed_rpm', 'torque_nm',
                      'air_temperature_k', 'process_temperature_k', 'tool_wear_min']
text_features = []
for feature in categorical_features:
    ml_dataset[feature] = ml_dataset[feature].apply(coerce_to_unicode)
for feature in text_features:
    ml_dataset[feature] = ml_dataset[feature].apply(coerce_to_unicode)
for feature in numerical_features:
    if ml_dataset[feature].dtype == np.dtype('M8[ns]') or (hasattr(ml_dataset[feature].dtype, 'base') and ml_dataset[feature].dtype.base == np.dtype('M8[ns]')):
        ml_dataset[feature] = datetime_to_epoch(ml_dataset[feature])
    else:
        ml_dataset[feature] = ml_dataset[feature].astype('double')

target_map = {'0': 0, '1': 1}
ml_dataset['__target__'] = ml_dataset['machine_failure'].map(
    str).map(target_map)
del ml_dataset['machine_failure']


# CROSS-VALIDATION STRATEGY
train, test = pdu.split_train_valid(ml_dataset, prop=0.8)
print('Train data has %i rows and %i columns' %
      (train.shape[0], train.shape[1]))
print('Test data has %i rows and %i columns' % (test.shape[0], test.shape[1]))

# FEATURE PREPROCESSING
drop_rows_when_missing = []
impute_when_missing = [{'feature': 'rotational_speed_rpm', 'impute_with': 'MEAN'}, {'feature': 'torque_nm', 'impute_with': 'MEAN'}, {
    'feature': 'air_temperature_k', 'impute_with': 'MEAN'}, {'feature': 'process_temperature_k', 'impute_with': 'MEAN'}, {'feature': 'tool_wear_min', 'impute_with': 'MEAN'}, ]

# Features for which we drop rows with missing values"
for feature in drop_rows_when_missing:
    train = train[train[feature].notnull()]
    test = test[test[feature].notnull()]
    print('Dropped missing records in %s' % feature)

# Features for which we impute missing values"
for feature in impute_when_missing:
    if feature['impute_with'] == 'MEAN':
        v = train[feature['feature']].mean()
    elif feature['impute_with'] == 'MEDIAN':
        v = train[feature['feature']].median()
    elif feature['impute_with'] == 'CREATE_CATEGORY':
        v = 'NULL_CATEGORY'
    elif feature['impute_with'] == 'MODE':
        v = train[feature['feature']].value_counts().index[0]
    elif feature['impute_with'] == 'CONSTANT':
        v = feature['value']
    train[feature['feature']] = train[feature['feature']].fillna(v)
    test[feature['feature']] = test[feature['feature']].fillna(v)
    print('Imputed missing values in feature %s with value %s' %
          (feature['feature'], coerce_to_unicode(v)))


LIMIT_DUMMIES = 100

categorical_to_dummy_encode = ['twf', 'osf', 'hdf', 'rnf', 'type', 'pwf']

# Only keep the top 100 values


def select_dummy_values(train, features):
    dummy_values = {}
    for feature in categorical_to_dummy_encode:
        values = [
            value
            for (value, _) in Counter(train[feature]).most_common(LIMIT_DUMMIES)
        ]
        dummy_values[feature] = values
    return dummy_values


def dummy_encode_dataframe(df):
    for (feature, dummy_values) in select_dummy_values(train, categorical_to_dummy_encode).items():
        for dummy_value in dummy_values:
            dummy_name = u'%s_value_%s' % (
                feature, coerce_to_unicode(dummy_value))
            df[dummy_name] = (df[feature] == dummy_value).astype(float)
            print(feature)

        del df[feature]
        # print('Dummy-encoded feature %s' % feature)


dummy_encode_dataframe(train)

dummy_encode_dataframe(test)

rescale_features = {'rotational_speed_rpm': 'AVGSTD', 'torque_nm': 'AVGSTD',
                    'air_temperature_k': 'AVGSTD', 'process_temperature_k': 'AVGSTD', 'tool_wear_min': 'AVGSTD'}
for (feature_name, rescale_method) in rescale_features.items():
    if rescale_method == 'MINMAX':
        _min = train[feature_name].min()
        _max = train[feature_name].max()
        scale = _max - _min
        shift = _min
    else:
        shift = train[feature_name].mean()
        scale = train[feature_name].std()
    if scale == 0.:
        del train[feature_name]
        del test[feature_name]
        print('Feature %s was dropped because it has no variance' % feature_name)
    else:
        print('Rescaled %s' % feature_name)
        train[feature_name] = (train[feature_name] -
                               shift).astype(np.float64) / scale
        test[feature_name] = (test[feature_name] -
                              shift).astype(np.float64) / scale


# MODELING
X_train = train.drop('__target__', axis=1).dropna()
X_test = test.drop('__target__', axis=1).dropna()

y_train = train['__target__']
y_test = test['__target__']

clf = RandomForestClassifier(
    n_estimators=90,
    random_state=1337,
    max_depth=8,
    min_samples_leaf=7,
    verbose=2
)


clf.class_weight = "balanced"
with track_elapsed_time("fit"):
    clf.fit(X_train, y_train)

with track_elapsed_time("predict"):
    _predictions = clf.predict(X_test)

with track_elapsed_time("predict_proba"):
    _probas = clf.predict_proba(X_test)


# Remove rows for which the target is unknown.
ml_dataset = ml_dataset[~ml_dataset['__target__'].isnull()]

ml_dataset['__target__'] = ml_dataset['__target__'].astype(np.int64)

predictions = pd.Series(
    data=_predictions, index=X_test.index, name='predicted_value')
cols = [
    u'probability_of_value_%s' % label
    for (_, label) in sorted([(int(target_map[label]), label) for label in target_map])
]
probabilities = pd.DataFrame(data=_probas, index=X_test.index, columns=cols)

# Build scored dataset
results_test = X_test.join(predictions, how='left')
results_test = results_test.join(probabilities, how='left')
results_test = results_test.join(test["__target__"], how='left')
results_test = results_test.rename(columns={'__target__': 'machine_failure'})

feature_importances_data = []
features = X_train.columns

print(features)

for feature_name, feature_importance in zip(features, clf.feature_importances_):
    feature_importances_data.append({
        'feature': feature_name,
        'importance': feature_importance
    })

# # Plot the results
# pd.DataFrame(feature_importances_data).set_index('feature').sort_values(by='importance')[-10::].plot(
#     title='Top 10 most important variables',
#     kind='barh',
#     figsize=(10, 6),
#     color='#348ABD',
#     alpha=0.6,
#     lw='1',
#     edgecolor='#348ABD',
#     grid=False,
# )

# STORE MODEL
with open("prod_model.pkl", "wb+") as p_file:
    p_file.write(pickle.dumps(clf))
