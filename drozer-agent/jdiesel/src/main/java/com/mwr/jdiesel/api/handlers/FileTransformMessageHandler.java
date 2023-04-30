package com.mwr.jdiesel.api.handlers;

import com.google.protobuf.ByteString;
import com.mwr.jdiesel.api.InvalidMessageException;
import com.mwr.jdiesel.api.Protobuf;
import com.mwr.jdiesel.api.sessions.Session;

import java.io.FileInputStream;
import java.io.FileOutputStream;

public class FileTransformMessageHandler implements MessageHandler {
    private Session session = null;

    public FileTransformMessageHandler(Session session) {
        this.session = session;
    }

    @Override
    public Protobuf.Message handle(Protobuf.Message message) throws InvalidMessageException {
        if (message.getType() != Protobuf.Message.MessageType.FILE_TRANSFORM_REQUEST)
            throw new InvalidMessageException(message);
        if (!message.hasFileTransformRequest())
            throw new InvalidMessageException(message);
        if (!message.getFileTransformRequest().hasRemoteFilename())
            throw new InvalidMessageException(message);

        Protobuf.Message.FileTransformRequest req = message.getFileTransformRequest();
        boolean upload = req.getUpload();

        Protobuf.Message.FileTransformResponse.Builder resp = Protobuf.Message.FileTransformResponse.newBuilder();
        resp.setSessionId(session.getSessionId());
        resp.setSuccess(true);
        if (upload) {
            if (!req.hasData())
                throw new InvalidMessageException(message);

            String remoteFileName = req.getRemoteFilename();
            byte[] data = req.getData().toByteArray();

            try {
                FileOutputStream outputStream = new FileOutputStream(remoteFileName);
                outputStream.write(data);
                outputStream.close();
            } catch (Exception e) {
                resp.setSuccess(false);
            }
        } else {
            String remoteFileName = message.getFileTransformRequest().getRemoteFilename();

            try {
                FileInputStream inputStream = new FileInputStream(remoteFileName);
                byte[] data = new byte[inputStream.available()];
                inputStream.read(data);
                inputStream.close();
                resp.setData(ByteString.copyFrom(data));
            } catch (Exception e) {
                resp.setSuccess(false);
            }
        }
        return Protobuf.Message.newBuilder()
                .setId(message.getId())
                .setType(Protobuf.Message.MessageType.FILE_TRANSFORM_RESPONSE)
                .setFileTransformResponse(resp)
                .build();
    }
}
