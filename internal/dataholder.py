class DataHolder:
    def getdata(self):
        return self.__dict__

    def __str__(self):
        return str(self.getdata())

    def __repr__(self):
        return str(self)

    def __eq__(self, o):
        if not isinstance(o, DataHolder):
            return False
        return self.getdata() == o.getdata()
