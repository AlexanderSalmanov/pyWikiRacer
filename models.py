from sqlalchemy import Column, Integer, String, Table, ForeignKey
from sqlalchemy.orm import relationship 
from sqlalchemy.dialects import postgresql

from db import Base, engine

descendance = Table(
    'descendances', Base.metadata, 
    Column('parent_page_id', Integer, ForeignKey('wikipage.id'), primary_key=True),
    Column('child_page_id', Integer, ForeignKey('wikipage.id'), primary_key=True),
)

class WikiPage(Base):
    __tablename__ = 'wikipage' 
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(150))
    links = Column(postgresql.ARRAY(String))
    backlinks = Column(postgresql.ARRAY(String))
    
    level_two_children = relationship(      # this field is only relevant when we're going 2 levels deep
        'WikiPage',
        secondary=descendance,
        primaryjoin=id==descendance.c.parent_page_id,
        secondaryjoin=id==descendance.c.child_page_id
    )
    
    def add_child(self, page):
        if page not in self.level_two_children:
            self.level_two_children.append(page)
            
            
Base.metadata.create_all(engine)
