import asyncio
import random
import logging
import socket
from enum import Enum

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - Node %(node_id)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class NodeState(Enum):
    FOLLOWER = 'Follower'
    CANDIDATE = 'Candidate'
    LEADER = 'Leader'

class RaftNode:
    def __init__(self, node_id, total_nodes):
        self.node_id = node_id
        self.total_nodes = total_nodes
        
        self.current_term = 0
        self.voted_for = None
        self.state = NodeState.FOLLOWER
        
        self.election_timeout = random.uniform(1.5, 3.0)
        self.election_timer = 0
        self.vote_count = 0
        
        self.address = ('localhost', 5000 + node_id) # UDP address for node
        
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP socket
        self.socket.bind(self.address)
        self.socket.setblocking(False) # non blocking for async
        
        self.logger = logging.LoggerAdapter(
            logging.getLogger(__name__), 
            {'node_id': node_id}
        )

    async def start(self):
        receive_task = asyncio.create_task(self.receive_messages())
        state_task = asyncio.create_task(self.manage_state())
        await asyncio.gather(receive_task, state_task)

    async def manage_state(self):
        while True:
            await asyncio.sleep(0.5)
            
            # election timeout for non leader nodes
            if self.state != NodeState.LEADER:
                self.election_timer += 0.5
                
                # timeout triggers election
                if self.election_timer > self.election_timeout:
                    self.become_candidate()
            
            # leader sends periodic heartbeats
            if self.state == NodeState.LEADER:
                await self.send_heartbeats()

    def become_candidate(self):
        if self.state == NodeState.LEADER:
            return
        
        self.state = NodeState.CANDIDATE
        self.current_term += 1
        self.vote_count = 1
        self.voted_for = self.node_id
        self.election_timer = 0
        self.election_timeout = random.uniform(1.5, 3.0)
        
        self.logger.info(f"Became candidate in term {self.current_term}")
        
        # broadcast vote requests
        for node in range(self.total_nodes):
            if node != self.node_id:
                self.send_vote_request(node)

    def send_vote_request(self, target_node):
        message = f"VOTE_REQUEST {self.node_id} {self.current_term}".encode()
        try:
            self.socket.sendto(message, ('localhost', 5000 + target_node))
        except Exception as e:
            self.logger.error(f"Error sending vote request: {e}")

    async def send_heartbeats(self):
        if self.state != NodeState.LEADER:
            return
        
        for node in range(self.total_nodes):
            if node != self.node_id:
                message = f"HEARTBEAT {self.node_id} {self.current_term}".encode()
                try:
                    self.socket.sendto(message, ('localhost', 5000 + node))
                except Exception as e:
                    self.logger.error(f"Error sending heartbeat: {e}")
        
        # sleep to control heartbeat frequency
        await asyncio.sleep(1)

    async def receive_messages(self):
        # receive and process UDP messages
        loop = asyncio.get_running_loop()
        
        while True:
            try:
                # non blocking operations
                message, addr = await loop.sock_recvfrom(self.socket, 1024)
                message = message.decode()
                self.process_message(message, addr[0], addr[1])
            except asyncio.CancelledError:
                break
            except Exception as e:
                await asyncio.sleep(0.1)

    def process_message(self, message, sender_host, sender_port):
        parts = message.split()
        msg_type, sender_id = parts[0], int(parts[1])
        
        if msg_type == 'VOTE_REQUEST':
            sender_term = int(parts[2])
            self.handle_vote_request(sender_id, sender_term)
        
        elif msg_type == 'HEARTBEAT':
            sender_term = int(parts[2])
            self.handle_heartbeat(sender_id, sender_term)
        
        elif msg_type == 'VOTE_RESPONSE':
            sender_term = int(parts[2])
            self.handle_vote_response(sender_id, sender_term)

    def handle_vote_request(self, candidate_id, candidate_term):
        # decide whether to give vote to a candidate
        # update term if outdated
        if candidate_term > self.current_term:
            self.current_term = candidate_term
            self.state = NodeState.FOLLOWER
            self.voted_for = None
        
        # give vote
        if ((self.voted_for is None or self.voted_for == candidate_id) 
            and candidate_term >= self.current_term):
            self.voted_for = candidate_id
            self.election_timer = 0
            
            # send vote response
            response = f"VOTE_RESPONSE {self.node_id} {self.current_term}".encode()
            try:
                self.socket.sendto(response, ('localhost', 5000 + candidate_id))
                self.logger.info(f"Voted for candidate {candidate_id}")
            except Exception as e:
                self.logger.error(f"Error sending vote response: {e}")

    def handle_heartbeat(self, leader_id, leader_term):
        # handle received heartbeat
        if leader_term >= self.current_term:
            self.state = NodeState.FOLLOWER
            self.current_term = leader_term
            self.election_timer = 0
            self.voted_for = None
            self.logger.info(f"Received heartbeat from leader {leader_id}")

    def handle_vote_response(self, voter_id, voter_term):
        # process vote responses during election
        if self.state != NodeState.CANDIDATE or voter_term > self.current_term:
            return
        
        # increment vote count if valid
        self.vote_count += 1
        self.logger.info(f"Received vote from {voter_id}. Total votes: {self.vote_count}")
        
        if self.vote_count > self.total_nodes // 2:
            self.state = NodeState.LEADER
            self.logger.info(f"Elected as leader in term {self.current_term}")

async def main():
    total_nodes = 5
    nodes = [RaftNode(i, total_nodes) for i in range(total_nodes)]
    
    # each node in parallel
    await asyncio.gather(*(node.start() for node in nodes))

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Raft simulation stopped.")