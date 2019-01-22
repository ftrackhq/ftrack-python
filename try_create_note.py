import ftrack_api
session = ftrack_api.Session()

task = session.query('Task').first()
print task['id']

user = session.query('User').first()

category = session.query(
    'NoteCategory'
).first()



note = session.create('Note', {
    'content': 'New note with external category',
    'author': user,
    'category': category
})

task['notes'].append(note)

session.commit()