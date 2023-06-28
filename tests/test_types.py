from catflow_worker.types import (
    VideoFile,
    RawFrame,
    AnnotatedFrame,
    Prediction,
    EmbeddedFrame,
    Embedding,
    VideoFileSchema,
    RawFrameSchema,
    AnnotatedFrameSchema,
    PredictionSchema,
    EmbeddedFrameSchema,
    EmbeddingSchema,
)


def test_VideoFile():
    test_obj = VideoFile(key="test.mp4")
    test_data = {"key": "test.mp4"}

    schema = VideoFileSchema()
    loaded = schema.load(test_data)
    assert isinstance(loaded, VideoFile)

    dumped = schema.dump(test_obj)
    assert test_data == dumped


def test_RawFrame():
    test_obj = RawFrame(key="test.png", source=VideoFile(key="test.mp4"))
    test_data = {"key": "test.png", "source": {"key": "test.mp4"}}

    schema = RawFrameSchema()
    loaded = schema.load(test_data)
    assert isinstance(loaded, RawFrame)

    dumped = schema.dump(test_obj)
    assert test_data == dumped


def test_Prediction():
    test_obj = Prediction(x=4, y=5, width=3, height=1, confidence=0.97, label="cat")
    test_data = {
        "x": 4,
        "y": 5,
        "width": 3,
        "height": 1,
        "confidence": 0.97,
        "label": "cat",
    }

    schema = PredictionSchema()
    loaded = schema.load(test_data)
    assert isinstance(loaded, Prediction)

    dumped = schema.dump(test_obj)
    assert test_data == dumped


def test_AnnotatedFrame():
    test_obj = AnnotatedFrame(
        key="test.png",
        source=VideoFile(key="test.mp4"),
        model_name="testmodel",
        predictions=[
            Prediction(x=4, y=5, width=3, height=1, confidence=0.97, label="cat"),
            Prediction(x=10, y=53, width=33, height=12, confidence=0.53, label="dog"),
        ],
    )
    test_data = {
        "key": "test.png",
        "model_name": "testmodel",
        "source": {"key": "test.mp4"},
        "predictions": [
            {
                "x": 4,
                "y": 5,
                "width": 3,
                "height": 1,
                "confidence": 0.97,
                "label": "cat",
            },
            {
                "x": 10,
                "y": 53,
                "width": 33,
                "height": 12,
                "confidence": 0.53,
                "label": "dog",
            },
        ],
    }

    schema = AnnotatedFrameSchema()
    loaded = schema.load(test_data)
    assert isinstance(loaded, AnnotatedFrame)

    dumped = schema.dump(test_obj)
    assert test_data == dumped


def test_Embedding():
    test_obj = Embedding(vector=[1, 2, 3, 4])
    test_data = {"vector": [1, 2, 3, 4]}

    schema = EmbeddingSchema()
    loaded = schema.load(test_data)
    assert isinstance(loaded, Embedding)

    dumped = schema.dump(test_obj)
    assert test_data == dumped


def test_EmbeddedFrame():
    test_obj = EmbeddedFrame(
        key="test.png",
        source=VideoFile(key="test.mp4"),
        embedding=Embedding(vector=[1, 2, 3, 4]),
    )
    test_data = {
        "key": "test.png",
        "source": {"key": "test.mp4"},
        "embedding": {"vector": [1, 2, 3, 4]},
    }

    schema = EmbeddedFrameSchema()
    loaded = schema.load(test_data)
    assert isinstance(loaded, EmbeddedFrame)

    dumped = schema.dump(test_obj)
    assert test_data == dumped
