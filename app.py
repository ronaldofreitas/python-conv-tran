from flask import Flask, request, jsonify
from pydub import AudioSegment
from google.cloud import storage
import os
storage_client = storage.Client()
bucket_destino = storage_client.get_bucket("catalobyte-output")
bucket_origem_apagar = storage_client.get_bucket("catalobyte-input")

app = Flask(__name__)

@app.route("/", methods=["POST"])
def receive():

    data = request.get_json()
    gs_uri = data['gs_uri'] # uri original do arquivo em 'catalobyte-input'
    index_manticore = data['index_manticore']
    foldername = data['foldername'] # firebase user uid
    file_id = data['file_id']
    idioma = data['idioma']
    trad_idom = data['idiotrad']
    full_path_uri = gs_uri.split('/')
    file_name_uri = full_path_uri[-1] # nome completo do arquivo
    nma = file_name_uri.split('-')
    samefile = nma[1] # datetime gerado na criação do arquivo, fica algo como '1627734238643.flac'

    # ATENÇÃO! só funciona uma chamada por vez, mais de uma chamada ao mesmo tempo pode apagar tudo dos demais
    tempfile = "temp.flac"
    destname = samefile+".flac"

    if not os.path.exists(tempfile):
        os.mknod(tempfile)
    with open(tempfile, 'wb+') as file_obj:
        storage_client.download_blob_to_file(gs_uri, file_obj)

    s = AudioSegment.from_file(tempfile)

    converted_file = s.set_channels(1).set_frame_rate(16000) #taxa de amostragem = biterate / framerate
    converted_file.export(destname, bitrate="16k", format="flac") #codec sem perdas = FLAC

    blob = bucket_destino.blob(foldername+'/'+index_manticore+'/'+file_id+'/'+destname)
    blob.upload_from_filename(destname)
    blob.metadata = {'x-goog-meta-item-idiom': idioma, 'x-goog-meta-item-trad': trad_idom}
    blob.patch()

    bucket_origem_apagar.delete_blob(foldername+'/'+file_name_uri)

    return "ok"

    '''
    if not os.path.exists(file_name_uri):
        os.mknod(file_name_uri)

        with open(file_name_uri, 'wb') as file_obj:
            storage_client.download_blob_to_file(gs_uri, file_obj)

        s = AudioSegment.from_file(file_name_uri)

        converted_file = s.set_channels(1).set_frame_rate(16000) #taxa de amostragem = biterate / framerate
        converted_file.export(dst, bitrate="16k", format="flac") #codec sem perdas = FLAC

        blob = bucket_destino.blob(foldername+'/'+index_manticore+'/'+file_id+'/'+destname)
        blob.upload_from_filename(dst)

        blob_del = bucket_origem_apagar.delete_blob(foldername+'/'+file_name_uri)

        return "ok"
    else: 
        return "not-ok"
    '''

if __name__ == "__main__":
    # Used when running locally only. When deploying to Cloud Run,
    # a webserver process such as Gunicorn will serve the app.
    app.run(host="localhost", port=8080, debug=True)
