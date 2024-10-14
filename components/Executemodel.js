// components/ExecuteModal.js
import React from "react";
import { Modal, Button } from "react-bootstrap";

const ExecuteModel = ({ show, handleClose, tokenPair, profit }) => {
  const handleConfirm = async () => {
    try {
      await executeTrade(tokenPair);
      handleClose();
    } catch (error) {
      console.error(error);
    }
  };

  return (
    <Modal show={show} onHide={handleClose}>
      <Modal.Header closeButton>
        <Modal.Title>Confirm Trade</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <p>Token Pair: {tokenPair}</p>
        <p>Expected Profit: {profit}%</p>
        <p>Do you want to execute this trade?</p>
      </Modal.Body>
      <Modal.Footer>
        <Button variant="secondary" onClick={handleClose}>Cancel</Button>
        <Button variant="primary" onClick={handleConfirm}>Confirm Trade</Button>
      </Modal.Footer>
    </Modal>
  );
};

export default ExecuteModel;
