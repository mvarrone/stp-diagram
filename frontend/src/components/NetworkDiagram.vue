<template>
    <div v-if="isLoading" class="loading-container">
        <div class="loading-message">
            <span class="loading-spinner"></span>
            Loading...
        </div>
    </div>
    <div v-else>
        <div v-if="errorMessage" class="error-message">
            {{ errorMessage }}
        </div>
        <div v-else>
            <div id="mynetwork"></div>
        </div>
    </div>
</template>

<script>
import axios from "axios";
import { Network } from 'vis-network';
// import { Network } from 'vue-visjs';
export default {
    name: "NetworkDiagram",
    components: {
        Network
    },
    data() {
        return {
            nodes: [],
            edges: [],
            isLoading: false,
            errorMessage: ''
        }
    },
    mounted() {
        this.getNodesAndEdges()
            .then(() => {
                // Create and configure the network
                const container = document.getElementById('mynetwork');
                const data = {
                    nodes: this.nodes,
                    edges: this.edges
                };
                var options = {
                    nodes: {
                        font: {
                            size: 15,
                            color: "#000000",
                        },
                        borderWidth: 1,
                        shadow: true
                    },
                    edges: {
                        smooth: {
                            type: "cubicBezier",
                            forceDirection: "vertical",
                            roundness: 0.5,
                        },
                    },
                    interaction: {
                        dragNodes: true,
                        tooltipDelay: 10,
                    },
                    layout: {
                        hierarchical: {
                            direction: "UD"
                        }
                    },
                    physics: {
                        enabled: true,
                        stabilization: false
                    },
                };
                const network = new Network(container, data, options);
            })
            .catch(err => {
                console.log(err);
            });
    },
    methods: {
        getNodesAndEdges() {
            this.isLoading = true;
            this.errorMessage = '';
            return axios
                .get("http://localhost:8000/graph/stp")
                .then(response => {
                    this.nodes = response.data.nodes;
                    this.edges = response.data.edges;
                })
                .catch(error => {
                    console.error("An error occurred:", error);
                    this.errorMessage = `An error occurred. Please, try again. Message: ${error.message}. Code: ${error.code}`;
                    this.isLoading = false;
                })
                .finally(() => {
                    this.isLoading = false;
                });
        }
    },

}
</script>

<style>
#mynetwork {
    width: auto;
    height: 800px;
    border: 1px solid lightgray;
}

h2 {
    text-align: center;
}

.loading-container {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100vh;
    /* Adjust as needed */
}

.loading-message {
    display: flex;
    flex-direction: column;
    align-items: center;
    font-size: 18px;
    color: #555;
}

.loading-spinner {
    display: inline-block;
    width: 24px;
    height: 24px;
    border-radius: 50%;
    border: 4px solid #ccc;
    border-top-color: #888;
    animation: spin 1s ease-in-out infinite;
    margin-bottom: 8px;
}

@keyframes spin {
    0% {
        transform: rotate(0deg);
    }

    100% {
        transform: rotate(360deg);
    }
}

.error-message {
    margin: 16px;
    padding: 16px;
    background-color: #ffdddd;
    color: #ff0000;
    border: 1px solid #ff0000;
    border-radius: 4px;
}
</style>
  