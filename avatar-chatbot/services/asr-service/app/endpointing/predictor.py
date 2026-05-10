class EndpointPredictor:
    def __init__(self, config):
        self.config = config
        
    def should_finalize(self, silence_duration: float) -> bool:
        return silence_duration > self.config.silence_threshold




