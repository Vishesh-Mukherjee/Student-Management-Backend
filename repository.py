from sqlite3 import Connection
from logging import Logger
from uuid import uuid4
from constant import Constant


class BasicRepository:

    def __init__(self, conn: Connection, tableName: str, logger: Logger):
        self._conn = conn
        self._tableName = tableName
        self._logger = logger
    
    def save(self, dataDict: dict):
        if Constant.ID in dataDict.keys() and self.existsByAttribute({Constant.ID: dataDict[Constant.ID]}):
            id = dataDict[Constant.ID]
            query = self._generateUpdateQuery(dataDict.keys())
            argument = [x for x in dataDict.values() if x != id]
            argument.append(id)
            self._logger.debug(f'Executing update query: [{query}], arguments: {argument}')
        else:
            if not Constant.ID in dataDict.keys():
                dataDict[Constant.ID] = str(uuid4())
            query = self._generateSaveQuery(dataDict.keys())
            argument = list(dataDict.values())
            self._logger.debug(f'Executing insert query: [{query}], arguments: {argument}')
        self._conn.execute(query, argument)
        return dataDict

    def findByAttribute(self, pairs: dict, separator: str = Constant.AND, wildCard = None):
        query = f"SELECT * FROM {self._tableName} {self._generateWhereClause(pairs.keys(), separator)} {'' if wildCard is None else wildCard}"
        argument = list(pairs.values()) 
        self._logger.debug(f'Executing select query: [{query}], arguments: {argument}')
        data = self._conn.execute(query, argument).fetchone()
        return None if data is None else dict(data)
    
    def existsByAttribute(self, pairs: dict, separator: str = Constant.AND):
        query = f"SELECT count(*) > 0 FROM {self._tableName} {self._generateWhereClause(pairs.keys(), separator)}"
        argument = list(pairs.values())
        self._logger.debug(f'Executing exists query: [{query}], arguments: {argument}')
        entityExists = self._conn.execute(query, argument).fetchone()[0]
        return True if entityExists == 1 else False

    def deleteByAttribute(self, pairs: dict, separator: str = Constant.AND):
        self._conn.execute(f"DELETE FROM {self._tableName} {self._generateWhereClause(pairs.keys(), separator)}", list(pairs.values()))

    def findAllByAttribute(self, pairs: dict, separator: str = Constant.AND):
        cursor = self._conn.execute(f"SELECT * FROM {self._tableName} {self._generateWhereClause(pairs.keys(), separator)}", list(pairs.values()))
        return [dict(x) for x in cursor.fetchall()]

    def countByAttribute(self, pairs: dict, separator: str = Constant.AND):
        return self._conn.execute(f"SELECT COUNT(*) FROM {self._tableName} {self._generateWhereClause(pairs.keys(), separator)}", list(pairs.values())).fetchone()[0]
    
    def _generateWhereClause(self, keys: list, separator: str = Constant.AND):
        return f"WHERE {f' {separator} '.join([f'{key} = ?' for key in keys])}"

    def _generateSaveQuery(self, keys: list):
        return f"INSERT INTO {self._tableName} ({', '.join(keys)}) VALUES ({', '.join('?' for x in range(len(keys)))})"
    
    def _generateUpdateQuery(self, keys: list):
        return f"UPDATE {self._tableName} SET {', '.join([f'{key} = ?' for key in keys if key != Constant.ID])} WHERE {Constant.ID} = ?"
    
    
class ClassRepository (BasicRepository):

    def __init__(self, conn: Connection, tableName: str, logger: Logger):
        super().__init__(conn, tableName, logger)

    def findAllAvailableClasses(self):
        cursor = self._conn.execute(f"SELECT * FROM {self._tableName} where {Constant.CURRENT_ENROLLMENT} <= {Constant.MAX_ENROLLMENT}")
        return [dict(x) for x in cursor.fetchall()]
        

class EnrollmentRepository (BasicRepository):

    def __init__(self, conn: Connection, tableName: str, logger: Logger):
        super().__init__(conn, tableName, logger)

    def waitingListPosition(self, classId: str, studentId: str):
        subQuery = f"SELECT student_id, ROW_NUMBER() OVER (ORDER BY {Constant.ENROLLED_ON}) pos FROM {self._tableName} WHERE {Constant.CLASS_ID} = ? AND {Constant.DROPPED} = false AND {Constant.WAITING_LIST} = true"
        query = f"SELECT pos from ({subQuery}) where {Constant.STUDENT_ID} = ?"
        argument = [classId, studentId]
        self._logger.debug(f'Executing row number query: [{query}], arguments: {argument}')
        data = self._conn.execute(query, argument).fetchone()
        return None if data is None else data[0]
