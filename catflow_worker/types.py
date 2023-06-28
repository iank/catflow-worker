from marshmallow import Schema, fields, post_load


class VideoFile:
    """Class representing a video file stored in S3"""

    def __init__(self, key):
        self.key = key

    def __str__(self):
        return "<VideoFile(key={self.key})>".format(self=self)


class VideoFileSchema(Schema):
    key = fields.Str()

    @post_load
    def make_videofile(self, data, **kwargs):
        return VideoFile(**data)


class RawFrame:
    """Class representing a frame (image file stored in S3)"""

    def __init__(self, key, source):
        self.key = key
        self.source = source

    def __str__(self):
        return "<RawFrame(key={self.key},source={self.source!s})>".format(self=self)


class RawFrameSchema(Schema):
    key = fields.Str()
    source = fields.Nested(VideoFileSchema)

    @post_load
    def make_rawframe(self, data, **kwargs):
        return RawFrame(**data)


class Prediction:
    """Class representing a YOLO prediction"""

    def __init__(self, x, y, width, height, confidence, label):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.confidence = confidence
        self.label = label

    def __str__(self):
        return (
            "<Prediction(\n"
            "    x={self.x},y={self.y},width={self.width},height={self.height},\n"
            "    confidence={self.confidence},label={self.label}\n"
            ")>".format(self=self)
        )


class PredictionSchema(Schema):
    x = fields.Float()
    y = fields.Float()
    width = fields.Float()
    height = fields.Float()
    confidence = fields.Float()
    label = fields.Str()

    @post_load
    def make_prediction(self, data, **kwargs):
        return Prediction(**data)


class AnnotatedFrame:
    """Class representing an annotated frame (frame w/ predictions)"""

    def __init__(self, key, source, model_name, predictions):
        self.key = key
        self.source = source
        self.model_name = model_name
        self.predictions = predictions

    def __str__(self):
        return (
            "<AnnotatedFrame(\n"
            "key={self.key},source={self.source!s},\n"
            "model_name={self.model_name},predictions=({n} predictions)\n"
            ")>"
        ).format(n=len(self.predictions), self=self)


class AnnotatedFrameSchema(Schema):
    key = fields.Str()
    source = fields.Nested(VideoFileSchema)
    model_name = fields.Str()
    predictions = fields.List(fields.Nested(PredictionSchema))

    @post_load
    def make_annotatedframe(self, data, **kwargs):
        return AnnotatedFrame(**data)


class Embedding:
    """Class representing a vector embedding"""

    def __init__(self, vector):
        self.vector = vector

    def __str__(self):
        return "<Embedding( [({n} elements)] )>".format(n=len(self.vector))


class EmbeddingSchema(Schema):
    vector = fields.List(fields.Float())

    @post_load
    def make_embedding(self, data, **kwargs):
        return Embedding(**data)


class EmbeddedFrame:
    """Class representing a frame w/ embedding"""

    def __init__(self, key, source, embedding):
        self.key = key
        self.source = source
        self.embedding = embedding

    def __str__(self):
        return (
            "<EmbeddedFrame(\n"
            "key={self.key},source={self.source!s},\n"
            "embedding={self.embedding!s})>".format(self=self)
        )


class EmbeddedFrameSchema(Schema):
    key = fields.Str()
    source = fields.Nested(VideoFileSchema)
    embedding = fields.Nested(EmbeddingSchema)

    @post_load
    def make_embeddedframe(self, data, **kwargs):
        return EmbeddedFrame(**data)
